from abc import ABC, abstractmethod

from src.domain.models.auth_code import AuthCode
from src.domain.models.introspection_result import IntrospectionResult
from src.domain.models.token_response import TokenResponse
from src.domain.models.user import User


class AuthService(ABC):
    @abstractmethod
    def register(self, username: str, password: str, rsi_handle: str) -> User: ...

    @abstractmethod
    def authenticate(self, username: str, password: str) -> TokenResponse: ...

    @abstractmethod
    def [REDACTED]_token(self, token: str) -> TokenResponse: ...

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
        """Generate a verification code and store it on the user. [REDACTED] the code."""
        ...

    @abstractmethod
    def confirm_verification(self, user_id: str) -> bool:
        """Fetch the user's RSI profile and check for the verification code. [REDACTED] True if verified."""
        ...

    @abstractmethod
    def authorize(self, username: str, password: str, redirect_uri: str, state: str) -> AuthCode:
        """Validate credentials and redirect_uri, generate a single-use authorization code."""
        ...

    @abstractmethod
    def update_user(self, user_id: str, updates: dict) -> User:
        """Update allowed profile fields for a user. [REDACTED] the updated user."""
        ...  # pragma: no cover

    @abstractmethod
    def exchange_code(self, code: str, redirect_uri: str) -> TokenResponse:
        """Exchange a valid authorization code for access + [REDACTED] tokens."""
        ...

    @abstractmethod
    def change_password(self, user_id: str, old_password: str, new_password: str) -> None:
        """Change password for a user [REDACTED] [REDACTED] the old password. [REDACTED] all [REDACTED] tokens."""
        ...

    @abstractmethod
    def reset_password(self, user_id: str, new_password: str) -> None:
        """Admin reset of a user's password. [REDACTED] all [REDACTED] tokens."""
        ...

    @abstractmethod
    def forgot_password(self, username: str, rsi_handle: str) -> str:
        """Generate a verification code for password reset via RSI bio. [REDACTED] the code."""
        ...

    @abstractmethod
    def confirm_forgot_password(self, username: str, rsi_handle: str, new_password: str) -> None:
        """Confirm forgot-password by [REDACTED] RSI bio for verification code, then reset password."""
        ...

    @abstractmethod
    def introspect_token(self, token: str) -> IntrospectionResult:
        """Validate a JWT access token and return the user's active status plus resolved claims."""
        ...
