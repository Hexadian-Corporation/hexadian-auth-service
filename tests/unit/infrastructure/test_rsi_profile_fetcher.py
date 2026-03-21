from unittest.mock import AsyncMock, MagicMock

import httpx

from src.infrastructure.adapters.outbound.http.rsi_profile_fetcher_impl import RsiProfileFetcherImpl


class TestRsiProfileFetcherImpl:
    def setup_method(self) -> None:
        self.mock_client = AsyncMock(spec=httpx.AsyncClient)
        self.fetcher = RsiProfileFetcherImpl(self.mock_client)

    async def test_invalid_handle_returns_none(self) -> None:
        assert await self.fetcher.fetch_profile_bio("ab") is None
        assert await self.fetcher.fetch_profile_bio("bad handle!") is None
        assert await self.fetcher.fetch_profile_bio("a" * 31) is None
        assert await self.fetcher.fetch_profile_bio("") is None
        assert await self.fetcher.fetch_profile_bio("../etc/passwd") is None

    async def test_successful_bio_extraction(self) -> None:
        html = """
        <html>
        <body>
        <div class="entry bio">
          <span class="label">Bio</span>
          <div class="value">This is my bio with verification-code-123</div>
        </div>
        </body>
        </html>
        """
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = html
        mock_response.url.host = "robertsspaceindustries.com"
        self.mock_client.get.return_value = mock_response

        bio = await self.fetcher.fetch_profile_bio("ValidHandle")

        assert bio == "This is my bio with verification-code-123"
        self.mock_client.get.assert_called_once_with(
            "https://robertsspaceindustries.com/citizens/ValidHandle",
            timeout=10.0,
            follow_redirects=True,
        )

    async def test_profile_not_found_returns_none(self) -> None:
        mock_response = MagicMock()
        mock_response.status_code = 404
        self.mock_client.get.return_value = mock_response

        assert await self.fetcher.fetch_profile_bio("NonExistent") is None

    async def test_http_error_returns_none(self) -> None:
        self.mock_client.get.side_effect = httpx.HTTPError("Connection error")

        assert await self.fetcher.fetch_profile_bio("ValidHandle") is None

    async def test_no_bio_element_returns_none(self) -> None:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "<html><body>No bio here</body></html>"
        self.mock_client.get.return_value = mock_response

        assert await self.fetcher.fetch_profile_bio("ValidHandle") is None

    async def test_bio_with_whitespace_is_stripped(self) -> None:
        html = '<div class="entry bio"><span class="label">Bio</span><div class="value">  spaced bio  </div></div>'
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = html
        mock_response.url.host = "robertsspaceindustries.com"
        self.mock_client.get.return_value = mock_response

        assert await self.fetcher.fetch_profile_bio("Handle123") == "spaced bio"

    async def test_redirect_to_different_host_returns_none(self) -> None:
        html = '<div class="entry bio"><div class="value">bio text</div></div>'
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = html
        mock_response.url.host = "evil.example.com"
        self.mock_client.get.return_value = mock_response

        assert await self.fetcher.fetch_profile_bio("ValidHandle") is None

    async def test_same_host_redirect_succeeds(self) -> None:
        html = '<div class="entry bio"><div class="value">bio text</div></div>'
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = html
        mock_response.url.host = "robertsspaceindustries.com"
        self.mock_client.get.return_value = mock_response

        assert await self.fetcher.fetch_profile_bio("ValidHandle") == "bio text"
