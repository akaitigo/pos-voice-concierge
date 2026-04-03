import { useCallback, useState } from "react";
import type { AliasRegistration, ProductSearchResult } from "../types";

interface ProductSearchProps {
	/** 元の認識テキスト（辞書登録時の spoken_form として使用） */
	readonly originalTranscript: string;
	/** 検索結果 */
	readonly searchResults: readonly ProductSearchResult[];
	/** 検索中かどうか */
	readonly isSearching: boolean;
	/** 検索エラー */
	readonly searchError: string | null;
	/** 辞書登録中かどうか */
	readonly isRegistering: boolean;
	/** 検索実行 */
	readonly onSearch: (query: string) => Promise<void>;
	/** 商品選択時（辞書登録を含む） */
	readonly onSelectCorrect: (product: ProductSearchResult, registration: AliasRegistration) => void;
	/** 検索パネルを閉じる */
	readonly onClose: () => void;
}

/**
 * 手動修正用の商品検索コンポーネント.
 *
 * 誤認識時に正しい商品を検索・選択し、
 * 表記ゆれ辞書への登録を行う。
 */
export function ProductSearch({
	originalTranscript,
	searchResults,
	isSearching,
	searchError,
	isRegistering,
	onSearch,
	onSelectCorrect,
	onClose,
}: ProductSearchProps): React.JSX.Element {
	const [searchQuery, setSearchQuery] = useState("");

	const handleInputChange = useCallback(
		(e: React.ChangeEvent<HTMLInputElement>) => {
			const value = e.target.value;
			setSearchQuery(value);
			void onSearch(value);
		},
		[onSearch],
	);

	const handleSelectProduct = useCallback(
		(product: ProductSearchResult) => {
			const registration: AliasRegistration = {
				spokenForm: originalTranscript,
				productId: product.productId,
				productName: product.productName,
			};
			onSelectCorrect(product, registration);
		},
		[originalTranscript, onSelectCorrect],
	);

	return (
		<dialog className="product-search" open aria-label="商品検索">
			<div className="product-search__header">
				<h2 className="product-search__heading">商品を手動で検索</h2>
				<button type="button" className="product-search__close" onClick={onClose} aria-label="検索を閉じる">
					<svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor" aria-hidden="true">
						<path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z" />
					</svg>
				</button>
			</div>
			<p className="product-search__original">
				認識テキスト: <strong>{originalTranscript}</strong>
			</p>
			<div className="product-search__input-wrapper">
				<input
					type="search"
					className="product-search__input"
					placeholder="商品名を入力して検索..."
					value={searchQuery}
					onChange={handleInputChange}
					aria-label="商品名検索"
				/>
				{isSearching && <span className="product-search__loading" aria-label="検索中" />}
			</div>

			{searchError && (
				<div className="product-search__error" role="alert">
					{searchError}
				</div>
			)}

			{isRegistering && <output className="product-search__registering">辞書に登録中...</output>}

			{searchResults.length > 0 && (
				<div className="product-search__results" aria-label="検索結果">
					{searchResults.map((product) => (
						<div key={product.productId} className="product-search__result-item">
							<button
								type="button"
								className="product-search__result-button"
								onClick={() => handleSelectProduct(product)}
								disabled={isRegistering}
								aria-label={`${product.productName} を正しい商品として選択`}
							>
								<span className="product-search__result-name">{product.productName}</span>
								<span className="product-search__result-details">
									{product.janCode && <span className="product-search__result-jan">JAN: {product.janCode}</span>}
									{product.price > 0 && <span className="product-search__result-price">&yen;{product.price}</span>}
								</span>
							</button>
						</div>
					))}
				</div>
			)}

			{searchQuery.length > 0 && !isSearching && searchResults.length === 0 && !searchError && (
				<p className="product-search__no-results">該当する商品が見つかりませんでした</p>
			)}
		</dialog>
	);
}
