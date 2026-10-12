from datetime import datetime, timezone
from decimal import Decimal
from urllib.parse import urlparse
import ipaddress
import socket
import time

import httpx

from .config import Settings
from .db import SupabaseRepository
from .extractors.jsonld import extract_product
from .url_safety import validate_public_url
from .whatsapp import WhatsAppNotifier


def fetch_html(url: str, settings: Settings) -> str:
    validate_public_url(url)
    # Validate every redirect target to avoid redirect-based SSRF.
    current_url = url
    for _ in range(5):
        validate_public_url(current_url)
        with httpx.Client(
            follow_redirects=False,
            timeout=settings.request_timeout_seconds,
            headers={"User-Agent": settings.user_agent, "Accept": "text/html"},
        ) as client:
            response = client.get(current_url)
        if response.is_redirect:
            location = response.headers.get("location")
            if not location:
                raise ValueError("Redirect response did not include a Location header.")
            from urllib.parse import urljoin
            current_url = urljoin(current_url, location)
            validate_public_url(current_url)
            continue
        response.raise_for_status()
        content_type = response.headers.get("content-type", "")
        if "text/html" not in content_type.lower():
            raise ValueError(f"Unexpected content type: {content_type}")
        if len(response.content) > 5_000_000:
            raise ValueError("Product page exceeds the 5 MB HTML limit.")
        return response.text
    raise ValueError("Too many product page redirects.")


def run_checks(settings: Settings) -> dict:
    repo = SupabaseRepository(
        settings.supabase_url, settings.supabase_service_role_key,
        timeout=settings.request_timeout_seconds,
    )
    notifier = WhatsAppNotifier(settings)
    started = datetime.now(timezone.utc).isoformat()
    run = repo.insert("price_check_runs", {"started_at": started, "status": "running"})
    run_id = run["id"] if run else None
    checked = succeeded = errors = 0

    try:
        products = repo.select(
            "products",
            {"select": "*", "is_active": "eq.true", "order": "created_at.asc"},
        )
        for product in products:
            checked += 1
            product_id = product["id"]
            try:
                html = fetch_html(product["url"], settings)
                extracted = extract_product(html)
                current = Decimal(str(extracted["price"]))
                currency = extracted["currency"]
                previous_value = product.get("current_price")
                previous = Decimal(str(previous_value)) if previous_value is not None else None

                # Keep observed page identity useful; the user can edit it later.
                update = {
                    "product_name": extracted["product_name"] or product["product_name"],
                    "image_url": extracted["image_url"] or product.get("image_url"),
                    "store_domain": urlparse(product["url"]).hostname,
                    "currency": currency,
                    "current_price": str(current),
                    "last_checked_at": datetime.now(timezone.utc).isoformat(),
                    "last_check_status": "success",
                    "last_error": None,
                }
                repo.insert("price_history", {
                    "product_id": product_id,
                    "price": str(current),
                    "currency": currency,
                    "availability": extracted["availability"],
                    "source": extracted["source"],
                    "checked_at": update["last_checked_at"],
                })
                repo.update("products", {"id": f"eq.{product_id}"}, update)
                succeeded += 1

                if previous is not None and currency == product.get("currency", "IDR") and current < previous:
                    # Unique key makes each observed downward step independently auditable.
                    checked_at = update["last_checked_at"]
                    notification_key = f"{product_id}:{previous}:{current}"
                    # Check-and-insert on the unique idempotency key so a rerun
                    # does not create another send for the same observed drop.
                    try:
                        repo.insert("notification_logs", {
                            "product_id": product_id,
                            "old_price": str(previous),
                            "new_price": str(current),
                            "currency": currency,
                            "channel": "whatsapp",
                            "idempotency_key": notification_key,
                            "status": "pending",
                        })
                    except httpx.HTTPStatusError as insert_exc:
                        if insert_exc.response.status_code == 409:
                            print(f"Duplicate notification suppressed for product {product_id}")
                            continue
                        raise
                    try:
                        provider_id = notifier.send_price_drop(
                            product_name=update["product_name"],
                            url=product["url"],
                            old_price=previous,
                            new_price=current,
                            currency=currency,
                        )
                        status = "sent" if provider_id else "failed"
                        repo.update("notification_logs", {"idempotency_key": f"eq.{notification_key}"}, {
                            "status": status,
                            "provider_message_id": provider_id,
                            "sent_at": datetime.now(timezone.utc).isoformat() if provider_id else None,
                            "error_message": None if provider_id else "WhatsApp is not configured; no message sent.",
                        })
                    except Exception as exc:
                        repo.update("notification_logs", {"idempotency_key": f"eq.{notification_key}"}, {
                            "status": "failed", "error_message": str(exc)[:1000],
                        })
                        errors += 1
                        print(f"Notification failed for product {product_id}: {exc}")
            except Exception as exc:
                errors += 1
                print(f"Price check failed for product {product_id}: {exc}")
                try:
                    repo.update("products", {"id": f"eq.{product_id}"}, {
                        "last_checked_at": datetime.now(timezone.utc).isoformat(),
                        "last_check_status": "error",
                        "last_error": str(exc)[:1000],
                    })
                except Exception as update_exc:
                    print(f"Failed to persist product error {product_id}: {update_exc}")
            time.sleep(settings.request_delay_seconds)

        status = "success" if errors == 0 else ("partial" if succeeded else "failed")
        summary = {"checked": checked, "succeeded": succeeded, "errors": errors}
        if run_id:
            repo.update("price_check_runs", {"id": f"eq.{run_id}"}, {
                "finished_at": datetime.now(timezone.utc).isoformat(),
                "status": status,
                "products_checked": checked,
                "products_succeeded": succeeded,
                "errors_count": errors,
                "summary": summary,
            })
        return summary
    finally:
        repo.close()
