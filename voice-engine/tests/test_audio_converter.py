"""AudioConverter のテスト."""

import wave
from io import BytesIO
from unittest.mock import patch

import numpy as np
import pytest

from pos_voice_concierge.audio_converter import (
    AudioConversionError,
    convert_to_wav,
    create_wav_from_pcm,
)


class TestConvertToWav:
    """convert_to_wav のテストケース."""

    def test_wav_format_returns_input_unchanged(self) -> None:
        wav_data = _create_test_wav()
        result = convert_to_wav(wav_data, input_format="wav")
        assert result == wav_data

    def test_ffmpeg_not_found_raises_error(self) -> None:
        with patch("pos_voice_concierge.audio_converter.subprocess.run", side_effect=FileNotFoundError):
            with pytest.raises(AudioConversionError, match="ffmpeg"):
                convert_to_wav(b"\x00" * 100, input_format="webm")

    def test_ffmpeg_failure_raises_error(self) -> None:
        mock_result = type("Result", (), {"returncode": 1, "stderr": b"error message", "stdout": b""})()
        with patch("pos_voice_concierge.audio_converter.subprocess.run", return_value=mock_result):
            with pytest.raises(AudioConversionError, match="音声変換に失敗"):
                convert_to_wav(b"\x00" * 100, input_format="webm")


class TestCreateWavFromPcm:
    """create_wav_from_pcm のテストケース."""

    def test_creates_valid_wav(self) -> None:
        pcm_data = np.zeros(16000, dtype=np.int16).tobytes()
        wav_data = create_wav_from_pcm(pcm_data, sample_rate=16000)

        buffer = BytesIO(wav_data)
        with wave.open(buffer, "rb") as wf:
            assert wf.getnchannels() == 1
            assert wf.getsampwidth() == 2
            assert wf.getframerate() == 16000
            assert wf.getnframes() == 16000

    def test_empty_pcm_data(self) -> None:
        wav_data = create_wav_from_pcm(b"", sample_rate=16000)
        buffer = BytesIO(wav_data)
        with wave.open(buffer, "rb") as wf:
            assert wf.getnframes() == 0


def _create_test_wav(
    duration_seconds: float = 1.0,
    sample_rate: int = 16000,
) -> bytes:
    """テスト用 WAV データを生成する."""
    num_samples = int(sample_rate * duration_seconds)
    samples = np.zeros(num_samples, dtype=np.int16)
    return create_wav_from_pcm(samples.tobytes(), sample_rate)
