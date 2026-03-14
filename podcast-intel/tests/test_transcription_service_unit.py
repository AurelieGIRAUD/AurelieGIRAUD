"""
Unit tests for TranscriptionService.

All network calls are mocked — no real audio is downloaded and no real
API is called. Follows the same style as the other _unit test files.
"""

import io
import sys
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, call

sys.path.insert(0, str(Path(__file__).parent.parent))

from services.transcription_service import TranscriptionService, TranscriptionError


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_audio_bytes(size_mb: float = 1.0) -> bytes:
    """Return dummy bytes of the requested size."""
    return b"\x00" * int(size_mb * 1024 * 1024)


def _mock_stream_response(content: bytes, status_code: int = 200):
    """
    Build a mock requests.Response that streams the given content.
    Mirrors the interface used by _stream_audio() (stream=True, iter_content).
    """
    mock_resp = MagicMock()
    mock_resp.status_code = status_code
    mock_resp.raise_for_status = MagicMock()

    # Slice content into 8 KB chunks the way iter_content does
    chunk_size = 8192
    chunks = [
        content[i : i + chunk_size]
        for i in range(0, max(len(content), 1), chunk_size)
    ]
    mock_resp.iter_content = MagicMock(return_value=iter(chunks))
    return mock_resp


def _mock_whisper_response(text: str = "This is the transcript."):
    """Build a mock requests.Response for the Whisper API."""
    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json.return_value = {"text": text}
    return mock_resp


# ---------------------------------------------------------------------------
# Initialisation
# ---------------------------------------------------------------------------

class TestTranscriptionServiceInit:

    def test_empty_api_key_raises_value_error(self):
        with pytest.raises(ValueError):
            TranscriptionService(api_key="")

    def test_stores_api_key(self):
        svc = TranscriptionService(api_key="sk-openai-test")
        assert svc.api_key == "sk-openai-test"

    def test_authorization_header_set_correctly(self):
        svc = TranscriptionService(api_key="sk-openai-test")
        assert svc.headers["Authorization"] == "Bearer sk-openai-test"

    def test_no_content_type_header(self):
        # requests sets multipart Content-Type automatically; we must not override it
        svc = TranscriptionService(api_key="sk-openai-test")
        assert "content-type" not in svc.headers
        assert "Content-Type" not in svc.headers


# ---------------------------------------------------------------------------
# Successful transcription
# ---------------------------------------------------------------------------

class TestSuccessfulTranscription:

    @patch("services.transcription_service.requests.post")
    @patch("services.transcription_service.requests.get")
    def test_returns_transcript_string(self, mock_get, mock_post):
        mock_get.return_value = _mock_stream_response(_make_audio_bytes(1.0))
        mock_post.return_value = _mock_whisper_response("Hello world transcript.")

        svc = TranscriptionService(api_key="sk-test")
        result = svc.transcribe("https://example.com/episode.mp3")

        assert result == "Hello world transcript."
        assert isinstance(result, str)

    @patch("services.transcription_service.requests.post")
    @patch("services.transcription_service.requests.get")
    def test_audio_streamed_with_stream_true(self, mock_get, mock_post):
        mock_get.return_value = _mock_stream_response(_make_audio_bytes(1.0))
        mock_post.return_value = _mock_whisper_response()

        svc = TranscriptionService(api_key="sk-test")
        svc.transcribe("https://example.com/ep.mp3")

        assert mock_get.call_args.kwargs.get("stream") is True

    @patch("services.transcription_service.requests.post")
    @patch("services.transcription_service.requests.get")
    def test_whisper_called_with_correct_model(self, mock_get, mock_post):
        mock_get.return_value = _mock_stream_response(_make_audio_bytes(1.0))
        mock_post.return_value = _mock_whisper_response()

        svc = TranscriptionService(api_key="sk-test")
        svc.transcribe("https://example.com/ep.mp3")

        assert mock_post.call_args.kwargs["data"]["model"] == "whisper-1"

    @patch("services.transcription_service.requests.post")
    @patch("services.transcription_service.requests.get")
    def test_whisper_called_with_authorization_header(self, mock_get, mock_post):
        mock_get.return_value = _mock_stream_response(_make_audio_bytes(1.0))
        mock_post.return_value = _mock_whisper_response()

        svc = TranscriptionService(api_key="sk-test-key")
        svc.transcribe("https://example.com/ep.mp3")

        headers_sent = mock_post.call_args.kwargs["headers"]
        assert headers_sent["Authorization"] == "Bearer sk-test-key"

    @patch("services.transcription_service.requests.post")
    @patch("services.transcription_service.requests.get")
    def test_audio_url_passed_to_get(self, mock_get, mock_post):
        mock_get.return_value = _mock_stream_response(_make_audio_bytes(1.0))
        mock_post.return_value = _mock_whisper_response()

        svc = TranscriptionService(api_key="sk-test")
        svc.transcribe("https://cdn.example.com/specific-episode.mp3")

        assert mock_get.call_args.args[0] == "https://cdn.example.com/specific-episode.mp3"


# ---------------------------------------------------------------------------
# API failure → TranscriptionError
# ---------------------------------------------------------------------------

class TestTranscriptionErrors:

    @patch("services.transcription_service.requests.get")
    def test_download_http_error_raises_transcription_error(self, mock_get):
        import requests as req_lib

        mock_resp = MagicMock()
        mock_resp.raise_for_status.side_effect = req_lib.exceptions.HTTPError("404 Not Found")
        mock_get.return_value = mock_resp

        svc = TranscriptionService(api_key="sk-test")
        with pytest.raises(TranscriptionError):
            svc.transcribe("https://example.com/missing.mp3")

    @patch("services.transcription_service.requests.get")
    def test_download_timeout_raises_transcription_error(self, mock_get):
        import requests as req_lib

        mock_get.side_effect = req_lib.exceptions.Timeout

        svc = TranscriptionService(api_key="sk-test")
        with pytest.raises(TranscriptionError, match="timed out"):
            svc.transcribe("https://example.com/ep.mp3")

    @patch("services.transcription_service.requests.post")
    @patch("services.transcription_service.requests.get")
    def test_whisper_http_error_raises_transcription_error(self, mock_get, mock_post):
        import requests as req_lib

        mock_get.return_value = _mock_stream_response(_make_audio_bytes(1.0))
        mock_post_resp = MagicMock()
        mock_post_resp.raise_for_status.side_effect = req_lib.exceptions.HTTPError(
            "401 Unauthorized"
        )
        mock_post.return_value = mock_post_resp

        svc = TranscriptionService(api_key="sk-test")
        with pytest.raises(TranscriptionError):
            svc.transcribe("https://example.com/ep.mp3")

    @patch("services.transcription_service.requests.post")
    @patch("services.transcription_service.requests.get")
    def test_whisper_timeout_raises_transcription_error(self, mock_get, mock_post):
        import requests as req_lib

        mock_get.return_value = _mock_stream_response(_make_audio_bytes(1.0))
        mock_post.side_effect = req_lib.exceptions.Timeout

        svc = TranscriptionService(api_key="sk-test")
        with pytest.raises(TranscriptionError, match="timed out"):
            svc.transcribe("https://example.com/ep.mp3")

    @patch("services.transcription_service.requests.post")
    @patch("services.transcription_service.requests.get")
    def test_malformed_whisper_response_raises_transcription_error(self, mock_get, mock_post):
        mock_get.return_value = _mock_stream_response(_make_audio_bytes(1.0))
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = {"unexpected_key": "oops"}  # no "text" key
        mock_post.return_value = mock_resp

        svc = TranscriptionService(api_key="sk-test")
        with pytest.raises(TranscriptionError):
            svc.transcribe("https://example.com/ep.mp3")


# ---------------------------------------------------------------------------
# Chunking path (audio > 25 MB)
# ---------------------------------------------------------------------------

class TestChunkingPath:

    @patch("services.transcription_service.requests.post")
    @patch("services.transcription_service.requests.get")
    def test_small_file_sends_single_request(self, mock_get, mock_post):
        """Files under 25 MB must be sent in a single Whisper request."""
        mock_get.return_value = _mock_stream_response(_make_audio_bytes(1.0))
        mock_post.return_value = _mock_whisper_response("single transcript")

        svc = TranscriptionService(api_key="sk-test")
        result = svc.transcribe("https://example.com/small.mp3")

        assert result == "single transcript"
        assert mock_post.call_count == 1

    @patch("services.transcription_service.requests.post")
    @patch("services.transcription_service.requests.get")
    def test_exactly_at_limit_sends_single_request(self, mock_get, mock_post):
        """A file of exactly 25 MB must not be split (limit is strictly >)."""
        mock_get.return_value = _mock_stream_response(_make_audio_bytes(25.0))
        mock_post.return_value = _mock_whisper_response("at-limit transcript")

        svc = TranscriptionService(api_key="sk-test")
        result = svc.transcribe("https://example.com/exact.mp3")

        assert result == "at-limit transcript"
        assert mock_post.call_count == 1

    @patch("services.transcription_service.requests.post")
    @patch("services.transcription_service.requests.get")
    def test_large_file_sends_multiple_requests(self, mock_get, mock_post):
        """A 48 MB file should be split into 2 chunks → 2 Whisper requests."""
        large_audio = _make_audio_bytes(48.0)
        mock_get.return_value = _mock_stream_response(large_audio)
        mock_post.return_value = _mock_whisper_response("chunk transcript")

        svc = TranscriptionService(api_key="sk-test")
        svc.transcribe("https://example.com/large.mp3")

        # 48 MB / 24 MB chunks = 2 requests
        assert mock_post.call_count == 2

    @patch("services.transcription_service.requests.post")
    @patch("services.transcription_service.requests.get")
    def test_large_file_transcripts_concatenated_in_order(self, mock_get, mock_post):
        """Chunk transcripts must be joined with a space in chunk order."""
        large_audio = _make_audio_bytes(48.0)
        mock_get.return_value = _mock_stream_response(large_audio)

        # Return different text for each chunk call
        mock_post.side_effect = [
            _mock_whisper_response("first chunk"),
            _mock_whisper_response("second chunk"),
        ]

        svc = TranscriptionService(api_key="sk-test")
        result = svc.transcribe("https://example.com/large.mp3")

        assert result == "first chunk second chunk"

    @patch("services.transcription_service.requests.post")
    @patch("services.transcription_service.requests.get")
    def test_72mb_file_sends_three_requests(self, mock_get, mock_post):
        """A 72 MB file should be split into 3 chunks → 3 Whisper requests."""
        large_audio = _make_audio_bytes(72.0)
        mock_get.return_value = _mock_stream_response(large_audio)
        mock_post.return_value = _mock_whisper_response("chunk")

        svc = TranscriptionService(api_key="sk-test")
        svc.transcribe("https://example.com/huge.mp3")

        # 72 MB / 24 MB chunks = 3 requests
        assert mock_post.call_count == 3
