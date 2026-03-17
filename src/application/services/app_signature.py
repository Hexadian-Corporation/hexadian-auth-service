import hashlib
import hmac


def sign_app_id(app_id: str, secret: str) -> str:
    return hmac.new(secret.encode(), app_id.encode(), hashlib.sha256).hexdigest()


def verify_app_signature(app_id: str, signature: str, secret: str) -> bool:
    expected = sign_app_id(app_id, secret)
    return hmac.compare_digest(expected, signature)
