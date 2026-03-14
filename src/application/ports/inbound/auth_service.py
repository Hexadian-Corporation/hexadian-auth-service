from abc import ABC, abstractmethod

from src.domain.models.user import User


class AuthService(ABC):

    @abstractmethod
    def register(self, username: str, email: str, password: str) -> User: ...

    @abstractmethod
    def authenticate(self, username: str, password: str) -> str: ...

    @abstractmethod
    def get_user(self, user_id: str) -> User: ...

    @abstractmethod
    def list_users(self) -> list[User]: ...

    @abstractmethod
    def delete_user(self, user_id: str) -> None: ...
