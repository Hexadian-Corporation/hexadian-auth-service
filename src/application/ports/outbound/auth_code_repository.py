from abc import ABC, abstractmethod

from src.domain.models.auth_code import AuthCode


class AuthCodeRepository(ABC):
    @abstractmethod
    async def save(self, auth_code: AuthCode) -> AuthCode: ...

    @abstractmethod
    async def find_by_code(self, code: str) -> AuthCode | None: ...

    @abstractmethod
    async def mark_used(self, code: str) -> None: ...
