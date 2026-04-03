"""gRPC サーバーのテスト.

モック音声データを使用した統合テスト。
"""

from unittest.mock import MagicMock

import numpy as np

from pos_voice_concierge.audio_converter import create_wav_from_pcm
from pos_voice_concierge.fuzzy_matcher import FuzzyMatcher
from pos_voice_concierge.generated import voice_service_pb2
from pos_voice_concierge.grpc_server import VoiceServiceServicer
from pos_voice_concierge.whisper_engine import TranscriptionResult


class MockTranscriptionEngine:
    """テスト用のモック音声認識エンジン."""

    def __init__(self, text: str = "コカコーラ 2本", confidence: float = 0.9) -> None:
        self._text = text
        self._confidence = confidence
        self._loaded = True

    def transcribe(self, audio_data: bytes) -> TranscriptionResult:
        return TranscriptionResult(
            text=self._text,
            confidence=self._confidence,
            language="ja",
        )

    def is_loaded(self) -> bool:
        return self._loaded


class TestVoiceServiceServicer:
    """VoiceServiceServicer のテストケース."""

    def setup_method(self) -> None:
        self.engine = MockTranscriptionEngine()
        self.matcher = FuzzyMatcher(threshold=70.0)
        self.matcher.register_product("P001", "コカ・コーラ 500ml")
        self.matcher.register_product("P002", "サントリー天然水 550ml")
        self.servicer = VoiceServiceServicer(self.engine, self.matcher)
        self.context = MagicMock()

    def test_recognize_returns_transcript(self) -> None:
        wav_data = _create_test_wav()
        request = voice_service_pb2.AudioData(
            data=wav_data,
            format="wav",
            sample_rate=16000,
        )

        result = self.servicer.Recognize(request, self.context)

        assert result.transcript == "コカコーラ 2本"
        assert result.confidence > 0.0
        assert result.is_final is True
        assert len(result.matches) > 0

    def test_recognize_with_product_match(self) -> None:
        wav_data = _create_test_wav()
        request = voice_service_pb2.AudioData(
            data=wav_data,
            format="wav",
            sample_rate=16000,
        )

        result = self.servicer.Recognize(request, self.context)

        assert len(result.matches) > 0
        assert result.matches[0].product_name == "コカ・コーラ 500ml"
        assert result.matches[0].product_id == "P001"

    def test_stream_recognize_processes_chunks(self) -> None:
        wav_data = _create_test_wav(duration_seconds=2.0)
        chunk_size = 1024
        chunks = []

        for i in range(0, len(wav_data), chunk_size):
            chunk_data = wav_data[i : i + chunk_size]
            chunks.append(
                voice_service_pb2.AudioChunk(
                    data=chunk_data,
                    format="wav",
                    sample_rate=16000,
                )
            )

        results = list(self.servicer.StreamRecognize(iter(chunks), self.context))

        assert len(results) > 0
        final_results = [r for r in results if r.is_final]
        assert len(final_results) > 0

    def test_stream_recognize_empty_stream(self) -> None:
        results = list(self.servicer.StreamRecognize(iter([]), self.context))

        assert len(results) == 1
        assert results[0].is_final is True
        assert results[0].transcript == ""

    def test_recognize_empty_transcript(self) -> None:
        self.engine._text = ""
        wav_data = _create_test_wav()
        request = voice_service_pb2.AudioData(
            data=wav_data,
            format="wav",
            sample_rate=16000,
        )

        result = self.servicer.Recognize(request, self.context)

        assert result.transcript == ""
        assert len(result.matches) == 0


def _create_test_wav(
    duration_seconds: float = 1.0,
    sample_rate: int = 16000,
) -> bytes:
    """テスト用 WAV データを生成する."""
    num_samples = int(sample_rate * duration_seconds)
    samples = np.zeros(num_samples, dtype=np.int16)
    return create_wav_from_pcm(samples.tobytes(), sample_rate)
