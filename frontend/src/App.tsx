import { useCallback, useEffect, useState } from "react";
import "./App.css";
import { MatchList } from "./components/MatchList";
import { MicButton } from "./components/MicButton";
import { ProductSearch } from "./components/ProductSearch";
import { QueryResultDisplay } from "./components/QueryResultDisplay";
import { TranscriptDisplay } from "./components/TranscriptDisplay";
import { useProductSearch } from "./hooks/useProductSearch";
import { useQuery } from "./hooks/useQuery";
import { useTts } from "./hooks/useTts";
import { useVoice } from "./hooks/useVoice";
import type { AliasRegistration, AliasRegistrationResponse, ProductMatch, ProductSearchResult } from "./types";

/** 確定済み商品の情報 */
interface ConfirmedProduct {
	readonly productId: string;
	readonly productName: string;
	readonly quantity: number;
}

/** 辞書登録のフィードバック */
interface AliasFeedback {
	readonly success: boolean;
	readonly message: string;
}

export function App(): React.JSX.Element {
	const { state, result, error, startListening, stopListening } = useVoice();
	const { ttsState, speak } = useTts();
	const { searchResults, isSearching, searchError, isRegistering, searchProducts, registerAlias, clearSearch } =
		useProductSearch();
	const { queryResult, isQuerying, queryError, executeQuery, clearQuery } = useQuery();

	const [selectedProductId, setSelectedProductId] = useState<string | null>(null);
	const [confirmedProduct, setConfirmedProduct] = useState<ConfirmedProduct | null>(null);
	const [showSearch, setShowSearch] = useState(false);
	const [aliasFeedback, setAliasFeedback] = useState<AliasFeedback | null>(null);

	const handleMicClick = useCallback((): void => {
		if (state === "idle" || state === "error") {
			setConfirmedProduct(null);
			setSelectedProductId(null);
			setShowSearch(false);
			setAliasFeedback(null);
			void startListening();
		} else {
			stopListening();
		}
	}, [state, startListening, stopListening]);

	const handleSelectMatch = useCallback(
		(match: ProductMatch): void => {
			setSelectedProductId(match.productId);
			setConfirmedProduct({
				productId: match.productId,
				productName: match.productName,
				quantity: match.quantity,
			});
			setShowSearch(false);
			speak(`${match.productName}、${String(match.quantity)}点で登録しました`);
		},
		[speak],
	);

	const handleOpenSearch = useCallback((): void => {
		setShowSearch(true);
		clearSearch();
	}, [clearSearch]);

	const handleCloseSearch = useCallback((): void => {
		setShowSearch(false);
		clearSearch();
	}, [clearSearch]);

	const handleSelectCorrect = useCallback(
		(product: ProductSearchResult, registration: AliasRegistration): void => {
			setConfirmedProduct({
				productId: product.productId,
				productName: product.productName,
				quantity: 1,
			});
			setSelectedProductId(product.productId);
			setShowSearch(false);

			speak(`${product.productName}に修正しました`);

			void registerAlias(registration).then((response: AliasRegistrationResponse) => {
				setAliasFeedback({
					success: response.success,
					message: response.success
						? `「${registration.spokenForm}」→「${product.productName}」を辞書に登録しました`
						: response.message,
				});
			});
		},
		[speak, registerAlias],
	);

	// 認識結果がfinalで、マッチなしの場合はクエリとして実行
	useEffect(() => {
		if (result?.isFinal && result.matches.length === 0 && result.transcript.length > 0) {
			void executeQuery(result.transcript);
		}
	}, [result, executeQuery]);

	// クエリ結果が出たらTTSで読み上げ
	useEffect(() => {
		if (queryResult) {
			speak(queryResult.responseText);
		}
	}, [queryResult, speak]);

	const handleReset = useCallback((): void => {
		setConfirmedProduct(null);
		setSelectedProductId(null);
		setShowSearch(false);
		setAliasFeedback(null);
		clearQuery();
	}, [clearQuery]);

	return (
		<div className="pos-voice-concierge">
			<header className="pos-voice-concierge__header">
				<h1 className="pos-voice-concierge__title">POS Voice Concierge</h1>
			</header>

			<div className="pos-voice-concierge__controls">
				<MicButton state={state} onClick={handleMicClick} />
				{ttsState === "speaking" && <output className="pos-voice-concierge__tts-status">読み上げ中...</output>}
			</div>

			{error && (
				<div className="error-display" role="alert">
					<p>{error}</p>
				</div>
			)}

			{result && <TranscriptDisplay result={result} />}

			{result && result.matches.length > 0 && !confirmedProduct && (
				<>
					<MatchList matches={result.matches} onSelect={handleSelectMatch} selectedProductId={selectedProductId} />
					<button type="button" className="match-list__correct-button" onClick={handleOpenSearch}>
						正しい商品が見つからない場合はこちら
					</button>
				</>
			)}

			{showSearch && result && (
				<ProductSearch
					originalTranscript={result.transcript}
					searchResults={searchResults}
					isSearching={isSearching}
					searchError={searchError}
					isRegistering={isRegistering}
					onSearch={searchProducts}
					onSelectCorrect={handleSelectCorrect}
					onClose={handleCloseSearch}
				/>
			)}

			{confirmedProduct && (
				<output className="confirmed-product">
					<h2 className="confirmed-product__heading">商品確定</h2>
					<p className="confirmed-product__name">{confirmedProduct.productName}</p>
					<p className="confirmed-product__quantity">数量: {confirmedProduct.quantity}</p>
					<button type="button" className="confirmed-product__reset" onClick={handleReset}>
						クリア
					</button>
				</output>
			)}

			{aliasFeedback && (
				<output
					className={`alias-feedback ${aliasFeedback.success ? "alias-feedback--success" : "alias-feedback--error"}`}
				>
					{aliasFeedback.message}
				</output>
			)}

			{isQuerying && <p className="pos-voice-concierge__querying">クエリ実行中...</p>}
			{queryError && (
				<div className="error-display" role="alert">
					<p>{queryError}</p>
				</div>
			)}
			{queryResult && <QueryResultDisplay result={queryResult} />}
		</div>
	);
}
