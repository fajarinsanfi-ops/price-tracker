from decimal import Decimal
import pytest

from app.extractors.jsonld import extract_product, PriceExtractionError


def test_extract_product_offer_jsonld():
    html = """
    <html><head>
    <script type="application/ld+json">
    {
      "@context": "https://schema.org",
      "@type": "Product",
      "name": "Headphone Demo",
      "image": "https://shop.example/image.jpg",
      "offers": {
        "@type": "Offer",
        "price": "1250000",
        "priceCurrency": "IDR",
        "availability": "https://schema.org/InStock"
      }
    }
    </script>
    </head></html>
    """
    result = extract_product(html)
    assert result["product_name"] == "Headphone Demo"
    assert result["price"] == Decimal("1250000.00")
    assert result["currency"] == "IDR"
    assert result["source"] == "jsonld"


def test_invalid_price_raises():
    html = """
    <script type="application/ld+json">
    {"@type":"Product","name":"No price","offers":{"@type":"Offer","price":"Rp 1.000"}}
    </script>
    """
    with pytest.raises(PriceExtractionError):
        extract_product(html)
