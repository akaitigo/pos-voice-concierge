import { useCallback, useRef, useState } from "react";

/** TTS の状態 */
export type TtsState = "idle" | "speaking";

/** useTts フックの戻り値 */
export interface UseTtsReturn {
	/** 現在の TTS 状態 */
	readonly ttsState: TtsState;
	/** テキストを音声で読み上げる */
	readonly speak: (text: string) => void;
	/** 読み上げを停止する */
	readonly cancelSpeech: () => void;
}

/** useTts フックのオプション */
interface UseTtsOptions {
	/** 音声の言語 (デフォルト: ja-JP) */
	readonly lang?: string;
	/** 読み上げ速度 (デフォルト: 1.0) */
	readonly rate?: number;
}

/**
 * Web Speech API SpeechSynthesis を使った TTS フック.
 *
 * テキストを日本語音声で読み上げる。
 * 読み上げ中の状態管理と、読み上げ停止機能を提供する。
 */
export function useTts(options: UseTtsOptions = {}): UseTtsReturn {
	const { lang = "ja-JP", rate = 1.0 } = options;

	const [ttsState, setTtsState] = useState<TtsState>("idle");
	const utteranceRef = useRef<SpeechSynthesisUtterance | null>(null);

	const speak = useCallback(
		(text: string) => {
			if (typeof window === "undefined" || !window.speechSynthesis) {
				return;
			}

			window.speechSynthesis.cancel();

			const utterance = new SpeechSynthesisUtterance(text);
			utterance.lang = lang;
			utterance.rate = rate;

			utterance.onstart = () => {
				setTtsState("speaking");
			};

			utterance.onend = () => {
				setTtsState("idle");
				utteranceRef.current = null;
			};

			utterance.onerror = () => {
				setTtsState("idle");
				utteranceRef.current = null;
			};

			utteranceRef.current = utterance;
			window.speechSynthesis.speak(utterance);
		},
		[lang, rate],
	);

	const cancelSpeech = useCallback(() => {
		if (typeof window === "undefined" || !window.speechSynthesis) {
			return;
		}
		window.speechSynthesis.cancel();
		setTtsState("idle");
		utteranceRef.current = null;
	}, []);

	return {
		ttsState,
		speak,
		cancelSpeech,
	};
}
