from abc import ABC, abstractmethod

from src.domain.models.auth_code import AuthCode


class AuthCodeRepository(ABC):
    @abstractmethod
    def save(self, auth_code: AuthCode) -> AuthCode: ...

    @abstractmethod
    def find_by_code(self, code: str) -> AuthCode | None: ...

    @abstractmethod
    def mark_used(self, code: str) -> None: ...
