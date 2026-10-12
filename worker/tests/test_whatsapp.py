from decimal import Decimal
from app.whatsapp import rupiah


def test_rupiah_integer_format():
    assert rupiah(Decimal("1000000")) == "Rp1.000.000"


def test_rupiah_decimal_format():
    assert rupiah(Decimal("1234.50")) == "Rp1.234,50"
