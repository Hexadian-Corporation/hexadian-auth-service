from abc import ABC, abstractmethod


class RsiProfileFetcher(ABC):

    @abstractmethod
    def fetch_profile_bio(self, rsi_handle: str) -> str | None:
        """Fetch the bio/short-bio text from the citizen's RSI profile page.
        Returns None if the profile doesn't exist."""
        ...
