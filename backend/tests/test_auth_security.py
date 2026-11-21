import pytest
from app.core.security import create_access_token, get_password_hash, verify_password, decode_token


def test_password_hashing():
    raw = "SuperSecret123!"
    hashed = get_password_hash(raw)
    assert hashed != raw
    assert verify_password(raw, hashed) is True
    assert verify_password("WrongPassword", hashed) is False


def test_jwt_token_flow():
    user_id_str = "12345678-1234-5678-1234-567812345678"
    token = create_access_token(subject=user_id_str)
    assert isinstance(token, str)
    assert len(token) > 20

    payload = decode_token(token)
    assert payload is not None
    assert payload.get("sub") == user_id_str
