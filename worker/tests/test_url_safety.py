from unittest.mock import patch
import pytest

from app.url_safety import validate_public_url


def public_record(ip):
    return (None, None, None, None, (ip, 443))


def test_rejects_http():
    with pytest.raises(ValueError):
        validate_public_url("http://example.com/product")


def test_rejects_embedded_credentials():
    with pytest.raises(ValueError):
        validate_public_url("https://user:password@example.com/product")


@patch("app.url_safety.socket.getaddrinfo", return_value=[public_record("93.184.216.34")])
def test_accepts_public_https_url(mock_dns):
    assert validate_public_url("https://example.com/product") == "example.com"


@patch("app.url_safety.socket.getaddrinfo", return_value=[public_record("127.0.0.1")])
def test_rejects_private_ip(mock_dns):
    with pytest.raises(ValueError):
        validate_public_url("https://example.com/product")
