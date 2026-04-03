import type { VoiceState } from "../types";

interface MicButtonProps {
	readonly state: VoiceState;
	readonly onClick: () => void;
}

const STATE_LABELS: Record<VoiceState, string> = {
	idle: "音声入力開始",
	listening: "停止",
	processing: "停止",
	error: "音声入力開始",
};

const STATE_TEXT: Record<VoiceState, string> = {
	idle: "音声入力",
	listening: "録音中...",
	processing: "処理中...",
	error: "再試行",
};

/**
 * マイクボタンコンポーネント.
 *
 * 録音状態に応じて視覚フィードバックを提供する。
 * - idle: マイクアイコン
 * - listening: パルスアニメーション付き録音中表示
 * - processing: スピナー付き処理中表示
 * - error: 再試行ボタン
 */
export function MicButton({ state, onClick }: MicButtonProps): React.JSX.Element {
	const isActive = state === "listening" || state === "processing";

	return (
		<button
			type="button"
			className={`mic-button mic-button--${state}`}
			onClick={onClick}
			aria-label={STATE_LABELS[state]}
			disabled={state === "processing"}
		>
			<span className="mic-button__icon" aria-hidden="true">
				{state === "processing" ? (
					<span className="mic-button__spinner" />
				) : (
					<svg viewBox="0 0 24 24" width="28" height="28" fill="currentColor" aria-hidden="true">
						{isActive ? (
							<rect x="6" y="6" width="12" height="12" rx="2" />
						) : (
							<>
								<path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z" />
								<path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z" />
							</>
						)}
					</svg>
				)}
			</span>
			<span className="mic-button__text">{STATE_TEXT[state]}</span>
			{state === "listening" && <span className="mic-button__pulse" aria-hidden="true" />}
		</button>
	);
}
