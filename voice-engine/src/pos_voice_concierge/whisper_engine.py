"""Whisper 音声認識エンジン.

OpenAI Whisper モデルを使用して音声→テキスト変換を行う。
"""

from __future__ import annotations

import io
import logging
from typing import Protocol

import numpy as np

logger = logging.getLogger(__name__)


class TranscriptionEngine(Protocol):
    """音声認識エンジンのプロトコル."""

    def transcribe(self, audio_data: bytes) -> TranscriptionResult:
        """音声データをテキストに変換する."""
        ...

    def is_loaded(self) -> bool:
        """モデルがロード済みかどうかを返す."""
        ...


class TranscriptionResult:
    """音声認識結果."""

    def __init__(self, text: str, confidence: float, language: str = "ja") -> None:
        """初期化.

        Args:
            text: 認識されたテキスト
            confidence: 信頼度 (0.0 - 1.0)
            language: 検出された言語コード
        """
        self.text = text
        self.confidence = confidence
        self.language = language


class WhisperEngine:
    """Whisper モデルによる音声認識エンジン.

    モデルのロードは初回呼び出し時に遅延実行される。
    """

    def __init__(self, model_name: str = "base") -> None:
        """初期化.

        Args:
            model_name: Whisper モデル名 ("tiny", "base", "small", "medium", "large")
        """
        self._model_name = model_name
        self._model = None

    def _ensure_model_loaded(self) -> None:
        """モデルがロードされていなければロードする."""
        if self._model is None:
            import whisper  # noqa: PLC0415

            logger.info("Whisper モデル '%s' をロード中...", self._model_name)
            self._model = whisper.load_model(self._model_name)
            logger.info("Whisper モデル '%s' のロード完了", self._model_name)

    def is_loaded(self) -> bool:
        """モデルがロード済みかどうかを返す."""
        return self._model is not None

    def transcribe(self, audio_data: bytes) -> TranscriptionResult:
        """WAV 音声データをテキストに変換する.

        Args:
            audio_data: WAV フォーマットの音声データ

        Returns:
            認識結果

        Raises:
            TranscriptionError: 認識に失敗した場合
        """
        self._ensure_model_loaded()

        try:
            audio_array = self._wav_bytes_to_float_array(audio_data)

            result = self._model.transcribe(
                audio_array,
                language="ja",
                fp16=False,
            )

            text = result.get("text", "").strip()
            segments = result.get("segments", [])
            avg_confidence = self._calculate_average_confidence(segments)

            return TranscriptionResult(
                text=text,
                confidence=avg_confidence,
                language="ja",
            )
        except Exception as e:
            msg = f"音声認識に失敗しました: {e}"
            raise TranscriptionError(msg) from e

    @staticmethod
    def _wav_bytes_to_float_array(wav_data: bytes) -> np.ndarray:
        """WAV バイト列を float32 の numpy 配列に変換する.

        Args:
            wav_data: WAV フォーマットのバイト列

        Returns:
            float32 の numpy 配列 (-1.0 ~ 1.0)
        """
        import wave  # noqa: PLC0415

        buffer = io.BytesIO(wav_data)
        with wave.open(buffer, "rb") as wf:
            frames = wf.readframes(wf.getnframes())
            return np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0

    @staticmethod
    def _calculate_average_confidence(segments: list[dict]) -> float:
        """セグメントから平均信頼度を算出する.

        Args:
            segments: Whisper の認識セグメント

        Returns:
            平均信頼度 (0.0 - 1.0)
        """
        if not segments:
            return 0.0

        probs = [seg.get("no_speech_prob", 0.0) for seg in segments]
        avg_no_speech = sum(probs) / len(probs)
        return max(0.0, 1.0 - avg_no_speech)


class TranscriptionError(Exception):
    """音声認識エラー."""
