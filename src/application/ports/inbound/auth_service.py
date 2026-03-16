from abc import ABC, abstractmethod

from src.domain.models.auth_code import AuthCode
from src.domain.models.token_response import TokenResponse
from src.domain.models.user import User


class AuthService(ABC):
    @abstractmethod
    def register(self, username: str, password: str, rsi_handle: str) -> User: ...

    @abstractmethod
    def authenticate(self, username: str, password: str) -> TokenResponse: ...

    @abstractmethod
    def refresh_token(self, token: str) -> TokenResponse: ...

    @abstractmethod
    def revoke_token(self, token: str) -> None: ...

    @abstractmethod
    def get_user(self, user_id: str) -> User: ...

    @abstractmethod
    def list_users(self) -> list[User]: ...

    @abstractmethod
    def delete_user(self, user_id: str) -> None: ...

    @abstractmethod
    def start_verification(self, user_id: str, rsi_handle: str) -> str:
        """Generate a verification code and store it on the user. Returns the code."""
        ...

    @abstractmethod
    def confirm_verification(self, user_id: str) -> bool:
        """Fetch the user's RSI profile and check for the verification code. Returns True if verified."""
        ...

    @abstractmethod
    def authorize(self, username: str, password: str, redirect_uri: str, state: str) -> AuthCode:
        """Validate credentials and redirect_uri, generate a single-use authorization code."""
        ...

    @abstractmethod
    def exchange_code(self, code: str, redirect_uri: str) -> TokenResponse:
        """Exchange a valid authorization code for access + refresh tokens."""
        ...
