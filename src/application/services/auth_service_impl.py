import hashlib
import re
import secrets

from src.application.ports.inbound.auth_service import AuthService
from src.application.ports.outbound.rsi_profile_fetcher import RsiProfileFetcher
from src.application.ports.outbound.user_repository import UserRepository
from src.domain.exceptions.user_exceptions import (
    InvalidCredentialsError,
    UserAlreadyExistsError,
    UserNotFoundError,
)
from src.domain.models.user import User

_RSI_HANDLE_PATTERN = re.compile(r"^[A-Za-z0-9_-]{3,30}$")


class AuthServiceImpl(AuthService):
    def __init__(self, repository: UserRepository, rsi_profile_fetcher: RsiProfileFetcher) -> None:
        self._repository = repository
        self._rsi_profile_fetcher = rsi_profile_fetcher

    def register(self, username: str, email: str, password: str) -> User:
        if self._repository.find_by_username(username) is not None:
            raise UserAlreadyExistsError(username)
        hashed = self._hash_password(password)
        user = User(username=username, email=email, hashed_password=hashed)
        return self._repository.save(user)

    def authenticate(self, username: str, password: str) -> str:
        user = self._repository.find_by_username(username)
        if user is None or not self._verify_password(password, user.hashed_password):
            raise InvalidCredentialsError()
        # TODO: Generate JWT token
        return f"token-{user.id}"

    def get_user(self, user_id: str) -> User:
        user = self._repository.find_by_id(user_id)
        if user is None:
            raise UserNotFoundError(user_id)
        return user

    def list_users(self) -> list[User]:
        return self._repository.find_all()

    def delete_user(self, user_id: str) -> None:
        if not self._repository.delete(user_id):
            raise UserNotFoundError(user_id)

    @staticmethod
    def _hash_password(password: str) -> str:
        salt = secrets.token_hex(16)
        hashed = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000)
        return f"{salt}:{hashed.hex()}"

    @staticmethod
    def _verify_password(password: str, hashed_password: str) -> bool:
        salt, expected_hash = hashed_password.split(":")
        actual_hash = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000)
        return secrets.compare_digest(actual_hash.hex(), expected_hash)

    def start_verification(self, user_id: str, rsi_handle: str) -> str:
        if not _RSI_HANDLE_PATTERN.match(rsi_handle):
            raise ValueError(f"Invalid RSI handle format: {rsi_handle}")

        user = self._repository.find_by_id(user_id)
        if user is None:
            raise UserNotFoundError(user_id)

        code = secrets.token_hex(16)
        user.rsi_handle = rsi_handle
        user.rsi_verification_code = code
        user.rsi_verified = False
        self._repository.save(user)
        return code

    def confirm_verification(self, user_id: str) -> bool:
        user = self._repository.find_by_id(user_id)
        if user is None:
            raise UserNotFoundError(user_id)

        if not user.rsi_handle or not user.rsi_verification_code:
            raise ValueError("Verification not started. Call start_verification first.")

        bio = self._rsi_profile_fetcher.fetch_profile_bio(user.rsi_handle)
        if bio is not None and user.rsi_verification_code in bio:
            user.rsi_verified = True
            self._repository.save(user)
            return True
        return False
