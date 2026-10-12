import json
import re
from decimal import Decimal, InvalidOperation
from typing import Any
from bs4 import BeautifulSoup


class PriceExtractionError(RuntimeError):
    pass


def _objects(value: Any):
    if isinstance(value, list):
        for item in value:
            yield from _objects(item)
    elif isinstance(value, dict):
        graph = value.get("@graph")
        if graph is not None:
            yield from _objects(graph)
        yield value


def _has_type(obj: dict, expected: str) -> bool:
    value = obj.get("@type", [])
    values = value if isinstance(value, list) else [value]
    return any(str(v).lower().endswith(expected.lower()) for v in values)


def _decimal_price(value: Any) -> Decimal | None:
    if value is None or isinstance(value, bool):
        return None
    # Schema.org prices should be numeric strings/numbers. Avoid guessing from
    # formatted display text such as "Rp 1.000.000" to prevent wrong parsing.
    try:
        result = Decimal(str(value).strip())
    except (InvalidOperation, ValueError):
        return None
    if not result.is_finite() or result <= 0:
        return None
    return result.quantize(Decimal("0.01"))


def extract_product(html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    candidates: list[dict] = []

    for script in soup.find_all("script", attrs={"type": re.compile(r"ld\+json", re.I)}):
        raw = script.string or script.get_text()
        if not raw or not raw.strip():
            continue
        try:
            data = json.loads(raw.strip())
        except json.JSONDecodeError:
            continue
        candidates.extend(
            obj for obj in _objects(data)
            if isinstance(obj, dict) and _has_type(obj, "Product")
        )

    for product in candidates:
        name = product.get("name")
        offers = product.get("offers")
        offer_list = offers if isinstance(offers, list) else [offers]
        for offer in offer_list:
            if not isinstance(offer, dict):
                continue
            price = _decimal_price(offer.get("price"))
            if price is None and isinstance(offer.get("priceSpecification"), dict):
                price = _decimal_price(
                    offer["priceSpecification"].get("price")
                )
            if price is None:
                continue
            currency = str(offer.get("priceCurrency") or "IDR").upper()
            if not re.fullmatch(r"[A-Z]{3}", currency):
                currency = "IDR"
            availability = offer.get("availability")
            image = product.get("image")
            if isinstance(image, list):
                image = image[0] if image else None
            if isinstance(image, dict):
                image = image.get("url")
            return {
                "product_name": str(name or "Produk tanpa nama").strip(),
                "price": price,
                "currency": currency,
                "availability": str(availability) if availability else None,
                "image_url": str(image) if image else None,
                "source": "jsonld",
            }

    raise PriceExtractionError(
        "No valid Product/Offer JSON-LD price was found. "
        "This store may need a store-specific extractor."
    )
