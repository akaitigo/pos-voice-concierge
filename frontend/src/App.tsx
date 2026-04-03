import { useState } from "react";

type RecognitionState = "idle" | "listening" | "processing";

export function App(): React.JSX.Element {
	const [state, setState] = useState<RecognitionState>("idle");
	const [transcript, setTranscript] = useState<string>("");

	const handleMicClick = (): void => {
		if (state === "idle") {
			setState("listening");
			setTranscript("");
		} else {
			setState("idle");
		}
	};

	return (
		<div className="pos-voice-concierge">
			<h1>POS Voice Concierge</h1>
			<button type="button" onClick={handleMicClick} aria-label={state === "listening" ? "停止" : "音声入力開始"}>
				{state === "idle" && "🎤 音声入力"}
				{state === "listening" && "⏹ 停止"}
				{state === "processing" && "⏳ 処理中..."}
			</button>
			{transcript && (
				<div className="transcript">
					<p>認識結果: {transcript}</p>
				</div>
			)}
		</div>
	);
}
