from unittest.mock import MagicMock, patch

from src.infrastructure.adapters.outbound.http.rsi_profile_fetcher_impl import RsiProfileFetcherImpl


class TestRsiProfileFetcherImpl:
    def setup_method(self) -> None:
        self.fetcher = RsiProfileFetcherImpl()

    def test_invalid_handle_returns_none(self) -> None:
        assert self.fetcher.fetch_profile_bio("ab") is None
        assert self.fetcher.fetch_profile_bio("bad handle!") is None
        assert self.fetcher.fetch_profile_bio("a" * 31) is None
        assert self.fetcher.fetch_profile_bio("") is None
        assert self.fetcher.fetch_profile_bio("../etc/passwd") is None

    @patch("src.infrastructure.adapters.outbound.http.rsi_profile_fetcher_impl.httpx.get")
    def test_successful_bio_extraction(self, mock_get: MagicMock) -> None:
        html = """
        <html>
        <body>
        <span class="value" id="bioval">This is my bio with verification-code-123</span>
        </body>
        </html>
        """
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = html
        mock_get.return_value = mock_response

        bio = self.fetcher.fetch_profile_bio("ValidHandle")

        assert bio == "This is my bio with verification-code-123"
        mock_get.assert_called_once_with(
            "https://robertsspaceindustries.com/citizens/ValidHandle",
            timeout=10.0,
            follow_redirects=True,
        )

    @patch("src.infrastructure.adapters.outbound.http.rsi_profile_fetcher_impl.httpx.get")
    def test_profile_not_found_returns_none(self, mock_get: MagicMock) -> None:
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        assert self.fetcher.fetch_profile_bio("NonExistent") is None

    @patch("src.infrastructure.adapters.outbound.http.rsi_profile_fetcher_impl.httpx.get")
    def test_http_error_returns_none(self, mock_get: MagicMock) -> None:
        import httpx

        mock_get.side_effect = httpx.HTTPError("Connection error")

        assert self.fetcher.fetch_profile_bio("ValidHandle") is None

    @patch("src.infrastructure.adapters.outbound.http.rsi_profile_fetcher_impl.httpx.get")
    def test_no_bio_element_returns_none(self, mock_get: MagicMock) -> None:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "<html><body>No bio here</body></html>"
        mock_get.return_value = mock_response

        assert self.fetcher.fetch_profile_bio("ValidHandle") is None

    @patch("src.infrastructure.adapters.outbound.http.rsi_profile_fetcher_impl.httpx.get")
    def test_bio_with_whitespace_is_stripped(self, mock_get: MagicMock) -> None:
        html = '<span class="value" id="bioval">  spaced bio  </span>'
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = html
        mock_get.return_value = mock_response

        assert self.fetcher.fetch_profile_bio("Handle123") == "spaced bio"
