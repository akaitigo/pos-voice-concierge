import type { ProductMatch } from "../types";

interface MatchListProps {
	readonly matches: readonly ProductMatch[];
	readonly onSelect: (match: ProductMatch) => void;
	readonly selectedProductId: string | null;
}

/**
 * マッチング候補リストコンポーネント.
 *
 * ファジーマッチングの候補をスコア順に表示し、
 * タップで商品を確定できる。
 */
export function MatchList({ matches, onSelect, selectedProductId }: MatchListProps): React.JSX.Element {
	if (matches.length === 0) {
		return (
			<div className="match-list match-list--empty">
				<p>マッチする商品が見つかりませんでした</p>
			</div>
		);
	}

	return (
		<div className="match-list">
			<h2 className="match-list__heading">商品候補</h2>
			<div className="match-list__items" aria-label="商品候補リスト">
				{matches.map((match) => {
					const isSelected = match.productId === selectedProductId;
					return (
						<div
							key={match.productId}
							className={`match-list__item ${isSelected ? "match-list__item--selected" : ""}`}
							data-selected={isSelected}
						>
							<button
								type="button"
								className="match-list__button"
								onClick={() => onSelect(match)}
								aria-label={`${match.productName} を選択 (スコア: ${String(Math.round(match.score))}%)`}
								aria-pressed={isSelected}
							>
								<span className="match-list__product-name">{match.productName}</span>
								<span className="match-list__details">
									<span className="match-list__score">スコア: {Math.round(match.score)}%</span>
									{match.quantity > 0 && <span className="match-list__quantity">数量: {match.quantity}</span>}
								</span>
							</button>
						</div>
					);
				})}
			</div>
		</div>
	);
}
