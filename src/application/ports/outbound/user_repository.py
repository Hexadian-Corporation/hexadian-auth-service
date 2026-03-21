from abc import ABC, abstractmethod

from src.domain.models.user import User


class UserRepository(ABC):
    @abstractmethod
    async def save(self, user: User) -> User: ...

    @abstractmethod
    async def find_by_id(self, user_id: str) -> User | None: ...

    @abstractmethod
    async def find_by_username(self, username: str) -> User | None: ...

    @abstractmethod
    async def find_by_rsi_handle(self, rsi_handle: str) -> User | None: ...

    @abstractmethod
    async def find_all(self) -> list[User]: ...

    @abstractmethod
    async def delete(self, user_id: str) -> bool: ...

    @abstractmethod
    async def update(self, user_id: str, fields: dict) -> User | None: ...
