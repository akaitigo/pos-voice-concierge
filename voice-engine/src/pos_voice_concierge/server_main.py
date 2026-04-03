"""Voice Engine サーバーエントリポイント."""

from __future__ import annotations

import logging
import os
import signal
import sys
from threading import Event

from pos_voice_concierge.fuzzy_matcher import FuzzyMatcher
from pos_voice_concierge.grpc_server import DEFAULT_PORT, create_server
from pos_voice_concierge.whisper_engine import WhisperEngine

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def main() -> None:
    """サーバーを起動する."""
    port = int(os.environ.get("VOICE_ENGINE_PORT", str(DEFAULT_PORT)))
    model_name = os.environ.get("WHISPER_MODEL", "base")

    engine = WhisperEngine(model_name=model_name)
    matcher = FuzzyMatcher(threshold=80.0)

    server = create_server(engine, matcher, port=port)
    server.start()
    logger.info("Voice Engine gRPC サーバー起動: port=%d, model=%s", port, model_name)

    shutdown_event = Event()

    def _handle_signal(_signum: int, _frame: object) -> None:
        logger.info("シャットダウンシグナル受信")
        shutdown_event.set()

    signal.signal(signal.SIGTERM, _handle_signal)
    signal.signal(signal.SIGINT, _handle_signal)

    shutdown_event.wait()

    logger.info("サーバーをシャットダウンしています...")
    server.stop(grace=5)
    logger.info("サーバーが停止しました")


if __name__ == "__main__":
    sys.exit(main())
