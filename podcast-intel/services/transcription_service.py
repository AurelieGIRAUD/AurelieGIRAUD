"""
Transcription service using OpenAI Whisper.

Single responsibility: Stream podcast audio and transcribe it to text.
Does NOT handle database, RSS, or intelligence extraction — pure transcription client.
"""

import io
import logging
from typing import Optional

import requests


logger = logging.getLogger(__name__)


class TranscriptionError(Exception):
    """Raised when audio transcription fails for any reason."""
    pass


class TranscriptionService:
    """
    Streams and transcribes podcast audio using OpenAI Whisper.

    Design principle: "Boring Pipelines"
    - Single responsibility: fetch audio, split if needed, transcribe
    - No files written to disk at any point — all processing is in memory
    - No ffmpeg or audio decoding — raw byte chunking only
    - Fail clearly with TranscriptionError; let the caller decide on fallback
    """

    WHISPER_API_URL = "https://api.openai.com/v1/audio/transcriptions"
    WHISPER_MODEL = "whisper-1"
    MAX_FILE_BYTES = 25 * 1024 * 1024  # 25 MB — Whisper API hard limit
    CHUNK_SIZE = 24 * 1024 * 1024      # 24 MB — safely under the limit

    def __init__(self, api_key: str):
        """
        Initialize TranscriptionService.

        Args:
            api_key: OpenAI API key

        Raises:
            ValueError: If api_key is empty
        """
        if not api_key:
            raise ValueError("OpenAI API key is required")

        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}"
        }

    def transcribe(self, audio_url: str) -> str:
        """
        Stream, optionally split, and transcribe audio from a URL.

        If the audio is under 25 MB it is sent as a single Whisper request.
        If the audio is over 25 MB it is split into 24 MB byte chunks, each
        chunk is transcribed separately, and the results are joined with a space.

        Args:
            audio_url: Direct URL to the podcast audio file

        Returns:
            Transcript as a plain text string

        Raises:
            TranscriptionError: If download or transcription fails
        """
        audio_data = self._stream_audio(audio_url)

        if len(audio_data) <= self.MAX_FILE_BYTES:
            return self._call_whisper(audio_data)

        chunks = self._split_into_chunks(audio_data)
        logger.info(
            f"Audio is {len(audio_data) / 1024 / 1024:.1f} MB — "
            f"splitting into {len(chunks)} chunks for Whisper transcription"
        )
        transcripts = [self._call_whisper(chunk) for chunk in chunks]
        return " ".join(transcripts)

    def _split_into_chunks(self, audio_data: bytes) -> list:
        """
        Split raw audio bytes into chunks of at most CHUNK_SIZE bytes.

        No decoding, no re-encoding, no ffmpeg — pure byte splitting.

        Args:
            audio_data: Raw audio bytes

        Returns:
            List of byte chunks, each at most CHUNK_SIZE bytes
        """
        return [
            audio_data[i:i + self.CHUNK_SIZE]
            for i in range(0, len(audio_data), self.CHUNK_SIZE)
        ]

    def _stream_audio(self, audio_url: str) -> bytes:
        """
        Stream audio file from URL directly into memory.

        Args:
            audio_url: URL to stream from

        Returns:
            Raw audio bytes

        Raises:
            TranscriptionError: If download fails or times out
        """
        try:
            response = requests.get(audio_url, stream=True, timeout=300)
            response.raise_for_status()

            buffer = io.BytesIO()
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    buffer.write(chunk)

            return buffer.getvalue()

        except requests.exceptions.Timeout:
            raise TranscriptionError(
                f"Audio download timed out after 300 seconds: {audio_url}"
            )
        except requests.exceptions.RequestException as e:
            raise TranscriptionError(
                f"Failed to download audio from {audio_url}: {str(e)}"
            )

    def _call_whisper(self, audio_data: bytes) -> str:
        """
        Send audio bytes to the OpenAI Whisper API and return the transcript.

        Args:
            audio_data: Audio bytes to transcribe

        Returns:
            Transcript text

        Raises:
            TranscriptionError: If the API call fails or returns an unexpected format
        """
        try:
            response = requests.post(
                self.WHISPER_API_URL,
                headers=self.headers,
                files={"file": ("audio.mp3", audio_data, "audio/mpeg")},
                data={"model": self.WHISPER_MODEL},
                timeout=600  # Long episodes can take several minutes to transcribe
            )
            response.raise_for_status()

        except requests.exceptions.Timeout:
            raise TranscriptionError("Whisper API request timed out after 600 seconds")
        except requests.exceptions.RequestException as e:
            raise TranscriptionError(f"Whisper API request failed: {str(e)}")

        try:
            return response.json()["text"]
        except (KeyError, ValueError) as e:
            raise TranscriptionError(
                f"Unexpected Whisper API response format: {str(e)}"
            )
