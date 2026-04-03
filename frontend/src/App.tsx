import { useVoice } from "./hooks/useVoice";
import type { ProductMatch } from "./hooks/useVoice";

export function App(): React.JSX.Element {
	const { state, result, error, startListening, stopListening } = useVoice();

	const handleMicClick = (): void => {
		if (state === "idle" || state === "error") {
			void startListening();
		} else {
			stopListening();
		}
	};

	return (
		<div className="pos-voice-concierge">
			<h1>POS Voice Concierge</h1>
			<button
				type="button"
				onClick={handleMicClick}
				aria-label={state === "listening" || state === "processing" ? "停止" : "音声入力開始"}
			>
				{state === "idle" && "🎤 音声入力"}
				{state === "listening" && "⏹ 停止"}
				{state === "processing" && "⏳ 処理中..."}
				{state === "error" && "🎤 再試行"}
			</button>
			{error && (
				<div className="error" role="alert">
					<p>{error}</p>
				</div>
			)}
			{result && (
				<div className="transcript">
					<p>認識結果: {result.transcript}</p>
					{result.confidence > 0 && <p>信頼度: {Math.round(result.confidence * 100)}%</p>}
					{result.matches.length > 0 && (
						<div className="matches">
							<h2>商品候補</h2>
							<ul>
								{result.matches.map((match: ProductMatch) => (
									<li key={match.productId}>
										{match.productName} (スコア: {Math.round(match.score)}%)
									</li>
								))}
							</ul>
						</div>
					)}
				</div>
			)}
		</div>
	);
}
