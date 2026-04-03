"""音声フォーマット変換モジュール.

WebM/Opus → WAV 変換をメモリ上で行う。
"""

from __future__ import annotations

import io
import subprocess
import wave

# Whisper が要求するサンプルレート
WHISPER_SAMPLE_RATE = 16000
WHISPER_CHANNELS = 1
WHISPER_SAMPLE_WIDTH = 2  # 16-bit


def convert_to_wav(audio_data: bytes, input_format: str = "webm") -> bytes:
    """音声データを WAV フォーマットに変換する.

    ffmpeg を使用してメモリ上で変換を行う。ディスクには書き出さない。

    Args:
        audio_data: 入力音声データのバイト列
        input_format: 入力フォーマット ("webm", "opus", "wav")

    Returns:
        WAV フォーマットのバイト列 (16kHz, mono, 16-bit)

    Raises:
        AudioConversionError: 変換に失敗した場合
    """
    if input_format == "wav":
        return audio_data

    try:
        result = subprocess.run(  # noqa: S603
            [  # noqa: S607
                "ffmpeg",
                "-i",
                "pipe:0",
                "-f",
                "wav",
                "-ar",
                str(WHISPER_SAMPLE_RATE),
                "-ac",
                str(WHISPER_CHANNELS),
                "-acodec",
                "pcm_s16le",
                "pipe:1",
            ],
            input=audio_data,
            capture_output=True,
            check=False,
            timeout=30,
        )
    except FileNotFoundError as e:
        msg = "ffmpeg が見つかりません。ffmpeg をインストールしてください。"
        raise AudioConversionError(msg) from e
    except subprocess.TimeoutExpired as e:
        msg = "音声変換がタイムアウトしました。"
        raise AudioConversionError(msg) from e

    if result.returncode != 0:
        msg = f"音声変換に失敗しました: {result.stderr.decode(errors='replace')}"
        raise AudioConversionError(msg)

    return result.stdout


def create_wav_from_pcm(pcm_data: bytes, sample_rate: int = WHISPER_SAMPLE_RATE) -> bytes:
    """PCM データから WAV ファイルを生成する.

    Args:
        pcm_data: PCM バイト列 (16-bit, mono)
        sample_rate: サンプルレート

    Returns:
        WAV フォーマットのバイト列
    """
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wf:
        wf.setnchannels(WHISPER_CHANNELS)
        wf.setsampwidth(WHISPER_SAMPLE_WIDTH)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm_data)
    return buffer.getvalue()


class AudioConversionError(Exception):
    """音声変換エラー."""
