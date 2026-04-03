"""WhisperEngine のテスト.

実際の Whisper モデルのダウンロードを避けるため、モックを使用する。
"""

from unittest.mock import MagicMock, patch

import numpy as np

from pos_voice_concierge.audio_converter import create_wav_from_pcm
from pos_voice_concierge.whisper_engine import TranscriptionResult, WhisperEngine


class TestWhisperEngine:
    """WhisperEngine のテストケース."""

    def test_is_loaded_returns_false_initially(self) -> None:
        engine = WhisperEngine(model_name="base")
        assert engine.is_loaded() is False

    @patch("pos_voice_concierge.whisper_engine.WhisperEngine._ensure_model_loaded")
    def test_transcribe_returns_result(self, mock_load) -> None:
        engine = WhisperEngine(model_name="base")
        mock_model = MagicMock()
        mock_model.transcribe.return_value = {
            "text": "コカコーラ 2本",
            "segments": [{"no_speech_prob": 0.1}],
        }
        engine._model = mock_model

        wav_data = _create_test_wav()
        result = engine.transcribe(wav_data)

        assert isinstance(result, TranscriptionResult)
        assert result.text == "コカコーラ 2本"
        assert result.confidence > 0.0
        assert result.language == "ja"

    @patch("pos_voice_concierge.whisper_engine.WhisperEngine._ensure_model_loaded")
    def test_transcribe_empty_audio(self, mock_load) -> None:
        engine = WhisperEngine(model_name="base")
        mock_model = MagicMock()
        mock_model.transcribe.return_value = {
            "text": "",
            "segments": [],
        }
        engine._model = mock_model

        wav_data = _create_test_wav()
        result = engine.transcribe(wav_data)

        assert result.text == ""
        assert result.confidence == 0.0

    def test_calculate_average_confidence(self) -> None:
        segments = [
            {"no_speech_prob": 0.1},
            {"no_speech_prob": 0.2},
            {"no_speech_prob": 0.3},
        ]
        confidence = WhisperEngine._calculate_average_confidence(segments)
        assert abs(confidence - 0.8) < 0.01

    def test_calculate_average_confidence_empty(self) -> None:
        confidence = WhisperEngine._calculate_average_confidence([])
        assert confidence == 0.0


def _create_test_wav(
    duration_seconds: float = 1.0,
    sample_rate: int = 16000,
) -> bytes:
    """テスト用 WAV データを生成する."""
    num_samples = int(sample_rate * duration_seconds)
    samples = np.zeros(num_samples, dtype=np.int16)
    return create_wav_from_pcm(samples.tobytes(), sample_rate)
