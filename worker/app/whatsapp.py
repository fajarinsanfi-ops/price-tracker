from datetime import datetime
from decimal import Decimal
from zoneinfo import ZoneInfo
import httpx

from .config import Settings


def rupiah(value: Decimal | str | int) -> str:
    amount = Decimal(str(value))
    if amount == amount.to_integral_value():
        return "Rp" + f"{int(amount):,}".replace(",", ".")
    return "Rp" + f"{amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


class WhatsAppNotifier:
    def __init__(self, settings: Settings):
        self.settings = settings

    def send_price_drop(
        self,
        *,
        product_name: str,
        url: str,
        old_price: Decimal,
        new_price: Decimal,
        currency: str,
    ) -> str | None:
        if not self.settings.whatsapp_enabled:
            print("WhatsApp not configured; notification skipped.")
            return None
        endpoint = (
            f"https://graph.facebook.com/"
            f"{self.settings.whatsapp_api_version}/"
            f"{self.settings.whatsapp_phone_number_id}/messages"
        )
        drop_pct = (old_price - new_price) / old_price * Decimal("100")
        if currency == "IDR":
            old_text, new_text = rupiah(old_price), rupiah(new_price)
        else:
            old_text, new_text = f"{old_price} {currency}", f"{new_price} {currency}"
        checked_at = datetime.now(ZoneInfo("Asia/Jakarta")).strftime("%d %B %Y, %H:%M WIB")
        params = [
            product_name[:500],
            old_text,
            new_text,
            f"{drop_pct:.2f}%",
            checked_at,
            url[:1000],
        ]
        payload = {
            "messaging_product": "whatsapp",
            "to": self.settings.whatsapp_recipient_number,
            "type": "template",
            "template": {
                "name": self.settings.whatsapp_template_name,
                "language": {"code": self.settings.whatsapp_template_language},
                "components": [{
                    "type": "body",
                    "parameters": [{"type": "text", "text": item} for item in params],
                }],
            },
        }
        with httpx.Client(timeout=20.0) as client:
            response = client.post(
                endpoint,
                headers={"Authorization": f"Bearer {self.settings.whatsapp_access_token}"},
                json=payload,
            )
            response.raise_for_status()
            body = response.json()
        messages = body.get("messages") or []
        return messages[0].get("id") if messages else None
