import re

import httpx

from src.application.ports.outbound.rsi_profile_fetcher import RsiProfileFetcher

_RSI_HANDLE_PATTERN = re.compile(r"^[A-Za-z0-9_-]{3,30}$")
_BIO_PATTERN = re.compile(
    r'<div\s+class="entry\s+bio">.*?<div\s+class="value">\s*(.*?)\s*</div>',
    re.DOTALL,
)


class RsiProfileFetcherImpl(RsiProfileFetcher):
    _ALLOWED_HOST = "robertsspaceindustries.com"

    def __init__(self, http_client: httpx.AsyncClient) -> None:
        self._client = http_client

    async def fetch_profile_bio(self, rsi_handle: str) -> str | None:
        if not _RSI_HANDLE_PATTERN.match(rsi_handle):
            return None

        url = f"https://robertsspaceindustries.com/citizens/{rsi_handle}"
        try:
            response = await self._client.get(url, timeout=10.0, follow_redirects=True)
        except httpx.HTTPError:
            return None

        if response.status_code != 200:
            return None

        if response.url.host != self._ALLOWED_HOST:
            return None

        match = _BIO_PATTERN.search(response.text)
        if match:
            return match.group(1).strip()
        return None
