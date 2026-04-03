import type { RecognitionResult } from "../types";

interface TranscriptDisplayProps {
	readonly result: RecognitionResult;
}

/**
 * 認識結果のリアルタイム表示コンポーネント.
 *
 * 音声認識のテキスト結果と信頼度を表示する。
 * isFinal でない場合は暫定結果として視覚的に区別する。
 */
export function TranscriptDisplay({ result }: TranscriptDisplayProps): React.JSX.Element {
	const confidencePercent = Math.round(result.confidence * 100);

	return (
		<output className="transcript-display" aria-live="polite">
			<h2 className="transcript-display__heading">認識結果</h2>
			<p className={`transcript-display__text ${result.isFinal ? "" : "transcript-display__text--interim"}`}>
				{result.transcript}
			</p>
			{result.confidence > 0 && (
				<div className="transcript-display__confidence">
					<span className="transcript-display__confidence-label">信頼度:</span>
					<span className="transcript-display__confidence-value">{confidencePercent}%</span>
					<progress
						className="transcript-display__confidence-bar"
						value={confidencePercent}
						max={100}
						aria-label={`信頼度 ${String(confidencePercent)}%`}
					>
						{confidencePercent}%
					</progress>
				</div>
			)}
			{!result.isFinal && <p className="transcript-display__interim-label">認識中...</p>}
		</output>
	);
}
