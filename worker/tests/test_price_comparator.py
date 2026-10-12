from decimal import Decimal
from app.price_checker import is_price_drop


def test_price_drop():
    assert is_price_drop(Decimal("1000000"), Decimal("900000"), "IDR", "IDR")


def test_no_alert_for_price_increase():
    assert not is_price_drop(Decimal("900000"), Decimal("950000"), "IDR", "IDR")


def test_no_alert_on_currency_change():
    assert not is_price_drop(Decimal("100"), Decimal("90"), "USD", "IDR")


def test_first_price_is_baseline():
    assert not is_price_drop(None, Decimal("900000"), "IDR", "IDR")
