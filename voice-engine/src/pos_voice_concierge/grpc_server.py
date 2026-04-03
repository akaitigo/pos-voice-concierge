"""gRPC 音声認識サーバー.

StreamRecognize RPC で音声ストリームを受信し、Whisper で認識した結果を返す。
"""

from __future__ import annotations

import logging
from concurrent import futures
from typing import TYPE_CHECKING

import grpc

from pos_voice_concierge.audio_converter import AudioConversionError, convert_to_wav
from pos_voice_concierge.generated import query_service_pb2_grpc, voice_service_pb2, voice_service_pb2_grpc
from pos_voice_concierge.query_service import QueryServiceServicer
from pos_voice_concierge.whisper_engine import TranscriptionError

if TYPE_CHECKING:
    from collections.abc import Iterator

    from pos_voice_concierge.fuzzy_matcher import FuzzyMatcher
    from pos_voice_concierge.product_repository import ProductRepository
    from pos_voice_concierge.whisper_engine import TranscriptionEngine

logger = logging.getLogger(__name__)

DEFAULT_PORT = 50051


class VoiceServiceServicer(voice_service_pb2_grpc.VoiceServiceServicer):
    """VoiceService gRPC サーバー実装."""

    def __init__(
        self,
        engine: TranscriptionEngine,
        matcher: FuzzyMatcher,
    ) -> None:
        """初期化.

        Args:
            engine: 音声認識エンジン
            matcher: 商品名ファジーマッチャー
        """
        self._engine = engine
        self._matcher = matcher

    def StreamRecognize(  # noqa: N802
        self,
        request_iterator: Iterator[voice_service_pb2.AudioChunk],
        context: grpc.ServicerContext,  # noqa: ARG002
    ) -> Iterator[voice_service_pb2.RecognitionResult]:
        """音声ストリーミング認識.

        クライアントから音声チャンクを受信し、認識結果を逐次返す。
        音声データはメモリ上のバッファのみで処理する。

        Args:
            request_iterator: 音声チャンクのイテレータ
            context: gRPC コンテキスト

        Yields:
            認識結果
        """
        audio_buffer = bytearray()
        audio_format = "webm"
        chunk_count = 0

        for chunk in request_iterator:
            audio_buffer.extend(chunk.data)
            chunk_count += 1

            if chunk.format:
                audio_format = chunk.format

            if len(audio_buffer) >= _MIN_BUFFER_SIZE:
                result = self._process_audio(bytes(audio_buffer), audio_format, is_final=False)
                if result is not None:
                    yield result
                audio_buffer.clear()

        if len(audio_buffer) > 0:
            result = self._process_audio(bytes(audio_buffer), audio_format, is_final=True)
            if result is not None:
                yield result
            else:
                yield voice_service_pb2.RecognitionResult(
                    transcript="",
                    confidence=0.0,
                    is_final=True,
                )
        else:
            yield voice_service_pb2.RecognitionResult(
                transcript="",
                confidence=0.0,
                is_final=True,
            )

        logger.info("ストリーミング認識完了: %d チャンク処理", chunk_count)

    def Recognize(  # noqa: N802
        self,
        request: voice_service_pb2.AudioData,
        context: grpc.ServicerContext,  # noqa: ARG002
    ) -> voice_service_pb2.RecognitionResult:
        """単発の音声認識.

        Args:
            request: 音声データ
            context: gRPC コンテキスト

        Returns:
            認識結果
        """
        result = self._process_audio(
            bytes(request.data),
            request.format or "webm",
            is_final=True,
        )
        if result is not None:
            return result

        return voice_service_pb2.RecognitionResult(
            transcript="",
            confidence=0.0,
            is_final=True,
        )

    def _process_audio(
        self,
        audio_data: bytes,
        audio_format: str,
        *,
        is_final: bool,
    ) -> voice_service_pb2.RecognitionResult | None:
        """音声データを処理して認識結果を返す.

        Args:
            audio_data: 音声バイト列
            audio_format: 音声フォーマット
            is_final: 最終結果かどうか

        Returns:
            認識結果。処理失敗時は None
        """
        try:
            wav_data = convert_to_wav(audio_data, audio_format)
            transcription = self._engine.transcribe(wav_data)

            matches = []
            if transcription.text:
                match_results = self._matcher.match(transcription.text)
                matches = [
                    voice_service_pb2.ProductMatch(
                        product_id=m.product_id,
                        product_name=m.product_name,
                        score=m.score,
                        quantity=1,
                    )
                    for m in match_results
                ]

            return voice_service_pb2.RecognitionResult(
                transcript=transcription.text,
                confidence=transcription.confidence,
                matches=matches,
                is_final=is_final,
            )
        except AudioConversionError:
            logger.exception("音声変換エラー")
            return None
        except TranscriptionError:
            logger.exception("音声認識エラー")
            return None


def create_server(
    engine: TranscriptionEngine,
    matcher: FuzzyMatcher,
    port: int = DEFAULT_PORT,
    max_workers: int = 4,
    repository: ProductRepository | None = None,
) -> grpc.Server:
    """gRPC サーバーを作成する.

    Args:
        engine: 音声認識エンジン
        matcher: 商品名ファジーマッチャー
        port: リッスンポート
        max_workers: ワーカースレッド数
        repository: 商品リポジトリ（DB接続時）

    Returns:
        設定済みの gRPC サーバー
    """
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=max_workers))
    servicer = VoiceServiceServicer(engine, matcher)
    voice_service_pb2_grpc.add_VoiceServiceServicer_to_server(servicer, server)

    query_servicer = QueryServiceServicer(matcher, repository)
    query_service_pb2_grpc.add_QueryServiceServicer_to_server(query_servicer, server)

    server.add_insecure_port(f"[::]:{port}")
    return server


# 中間結果を返す最小バッファサイズ (32KB)
_MIN_BUFFER_SIZE = 32 * 1024
