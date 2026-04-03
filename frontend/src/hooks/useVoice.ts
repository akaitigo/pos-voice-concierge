import { useCallback, useRef, useState } from "react";
import type { ProductMatch, RawProductMatchData, RawRecognitionData, RecognitionResult, VoiceState } from "../types";

export type { ProductMatch, RecognitionResult, VoiceState };

/** useVoice フックの戻り値 */
export interface UseVoiceReturn {
	/** 現在の状態 */
	readonly state: VoiceState;
	/** 最新の認識結果 */
	readonly result: RecognitionResult | null;
	/** エラーメッセージ */
	readonly error: string | null;
	/** 音声入力を開始する */
	readonly startListening: () => Promise<void>;
	/** 音声入力を停止する */
	readonly stopListening: () => void;
}

/** useVoice フックのオプション */
interface UseVoiceOptions {
	/** WebSocket URL (デフォルト: ws://localhost:8080/ws/voice) */
	readonly wsUrl?: string;
	/** 音声チャンクの送信間隔 (ms) */
	readonly chunkIntervalMs?: number;
}

const DEFAULT_WS_URL = "ws://localhost:8080/ws/voice";
const DEFAULT_CHUNK_INTERVAL_MS = 250;

/**
 * 音声入力・WebSocket送信・認識結果受信を管理するフック.
 *
 * Web Audio API + MediaRecorder でマイク入力をキャプチャし、
 * WebSocket でバイナリデータとして Backend に送信する。
 * 認識結果は JSON テキストメッセージとして受信する。
 * 音声データはメモリ上のストリーム処理のみで、ファイル保存しない。
 */
export function useVoice(options: UseVoiceOptions = {}): UseVoiceReturn {
	const { wsUrl = DEFAULT_WS_URL, chunkIntervalMs = DEFAULT_CHUNK_INTERVAL_MS } = options;

	const [state, setState] = useState<VoiceState>("idle");
	const [result, setResult] = useState<RecognitionResult | null>(null);
	const [error, setError] = useState<string | null>(null);

	const wsRef = useRef<WebSocket | null>(null);
	const mediaRecorderRef = useRef<MediaRecorder | null>(null);
	const streamRef = useRef<MediaStream | null>(null);

	const cleanupMediaRecorder = useCallback(() => {
		if (mediaRecorderRef.current) {
			if (mediaRecorderRef.current.state !== "inactive") {
				mediaRecorderRef.current.stop();
			}
			mediaRecorderRef.current = null;
		}
	}, []);

	const cleanupStream = useCallback(() => {
		if (streamRef.current) {
			for (const track of streamRef.current.getTracks()) {
				track.stop();
			}
			streamRef.current = null;
		}
	}, []);

	const cleanupWebSocket = useCallback(() => {
		if (wsRef.current) {
			if (wsRef.current.readyState === WebSocket.OPEN || wsRef.current.readyState === WebSocket.CONNECTING) {
				wsRef.current.close();
			}
			wsRef.current = null;
		}
	}, []);

	const cleanup = useCallback(() => {
		cleanupMediaRecorder();
		cleanupStream();
		cleanupWebSocket();
	}, [cleanupMediaRecorder, cleanupStream, cleanupWebSocket]);

	const startListening = useCallback(async () => {
		setError(null);
		setResult(null);

		try {
			const mediaStream = await navigator.mediaDevices.getUserMedia({
				audio: {
					channelCount: 1,
					sampleRate: 16000,
					echoCancellation: true,
					noiseSuppression: true,
				},
			});
			streamRef.current = mediaStream;

			const ws = new WebSocket(wsUrl);
			ws.binaryType = "arraybuffer";
			wsRef.current = ws;

			ws.onopen = () => {
				const recorder = new MediaRecorder(mediaStream, {
					mimeType: getSupportedMimeType(),
				});

				recorder.ondataavailable = (event: BlobEvent) => {
					if (event.data.size > 0 && ws.readyState === WebSocket.OPEN) {
						event.data.arrayBuffer().then(
							(buffer) => {
								ws.send(buffer);
							},
							() => {
								/* buffer conversion error - skip chunk */
							},
						);
					}
				};

				recorder.start(chunkIntervalMs);
				mediaRecorderRef.current = recorder;
				setState("listening");
			};

			ws.onmessage = (event: MessageEvent) => {
				try {
					const data = parseRecognitionResult(event.data as string);
					setResult(data);

					if (data.isFinal) {
						setState("processing");
					}
				} catch {
					/* ignore parse errors */
				}
			};

			ws.onerror = () => {
				setError("WebSocket接続エラーが発生しました");
				setState("error");
				cleanup();
			};

			ws.onclose = () => {
				if (state === "listening") {
					setState("idle");
				}
			};
		} catch (err: unknown) {
			const message = err instanceof Error ? err.message : "マイクへのアクセスに失敗しました";
			setError(message);
			setState("error");
			cleanup();
		}
	}, [wsUrl, chunkIntervalMs, cleanup, state]);

	const stopListening = useCallback(() => {
		cleanup();
		setState("idle");
	}, [cleanup]);

	return {
		state,
		result,
		error,
		startListening,
		stopListening,
	};
}

/** ブラウザがサポートする MIME タイプを取得する */
function getSupportedMimeType(): string {
	const types = ["audio/webm;codecs=opus", "audio/webm", "audio/ogg;codecs=opus"];

	for (const type of types) {
		if (MediaRecorder.isTypeSupported(type)) {
			return type;
		}
	}

	return "audio/webm";
}

/** JSON 文字列を RecognitionResult にパースする */
function parseRecognitionResult(json: string): RecognitionResult {
	const data = JSON.parse(json) as RawRecognitionData;

	return {
		transcript: String(data.transcript ?? ""),
		confidence: Number(data.confidence ?? 0),
		isFinal: Boolean(data.isFinal),
		matches: Array.isArray(data.matches)
			? (data.matches as RawProductMatchData[]).map((m) => ({
					productId: String(m.productId ?? ""),
					productName: String(m.productName ?? ""),
					score: Number(m.score ?? 0),
					quantity: Number(m.quantity ?? 0),
				}))
			: [],
	};
}
