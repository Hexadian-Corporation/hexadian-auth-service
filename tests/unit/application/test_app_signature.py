from src.application.services.app_signature import sign_app_id, verify_app_signature


class TestSignAppId:
    def test_returns_hex_string(self) -> None:
        result = sign_app_id("hhh-frontend", "my-secret")
        assert isinstance(result, str)
        assert len(result) == 64  # SHA-256 hex digest

    def test_deterministic(self) -> None:
        sig1 = sign_app_id("hhh-frontend", "my-secret")
        sig2 = sign_app_id("hhh-frontend", "my-secret")
        assert sig1 == sig2

    def test_different_app_ids_produce_different_sigs(self) -> None:
        sig1 = sign_app_id("hhh-frontend", "my-secret")
        sig2 = sign_app_id("hhh-backoffice", "my-secret")
        assert sig1 != sig2

    def test_different_secrets_produce_different_sigs(self) -> None:
        sig1 = sign_app_id("hhh-frontend", "secret-a")
        sig2 = sign_app_id("hhh-frontend", "secret-b")
        assert sig1 != sig2


class TestVerifyAppSignature:
    def test_valid_signature(self) -> None:
        sig = sign_app_id("hhh-frontend", "my-secret")
        assert verify_app_signature("hhh-frontend", sig, "my-secret") is True

    def test_invalid_signature(self) -> None:
        assert verify_app_signature("hhh-frontend", "bad-sig", "my-secret") is False

    def test_wrong_secret(self) -> None:
        sig = sign_app_id("hhh-frontend", "correct-secret")
        assert verify_app_signature("hhh-frontend", sig, "wrong-secret") is False

    def test_wrong_app_id(self) -> None:
        sig = sign_app_id("hhh-frontend", "my-secret")
        assert verify_app_signature("other-app", sig, "my-secret") is False
