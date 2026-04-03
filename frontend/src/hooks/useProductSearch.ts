import { useCallback, useRef, useState } from "react";
import type { AliasRegistration, AliasRegistrationResponse, ProductSearchResult, RawProductSearchData } from "../types";

/** useProductSearch フックの戻り値 */
export interface UseProductSearchReturn {
	/** 検索結果 */
	readonly searchResults: readonly ProductSearchResult[];
	/** 検索中かどうか */
	readonly isSearching: boolean;
	/** 検索エラー */
	readonly searchError: string | null;
	/** 辞書登録中かどうか */
	readonly isRegistering: boolean;
	/** 商品名で検索する */
	readonly searchProducts: (query: string) => Promise<void>;
	/** 表記ゆれ辞書に登録する */
	readonly registerAlias: (registration: AliasRegistration) => Promise<AliasRegistrationResponse>;
	/** 検索結果をクリアする */
	readonly clearSearch: () => void;
}

/** useProductSearch フックのオプション */
interface UseProductSearchOptions {
	/** 商品検索APIのベースURL */
	readonly apiBaseUrl?: string;
	/** デバウンス間隔 (ms) */
	readonly debounceMs?: number;
}

const DEFAULT_API_BASE_URL = "/api";
const DEFAULT_DEBOUNCE_MS = 300;

/** APIレスポンスをProductSearchResult配列にパースする */
function parseSearchResults(rawData: readonly RawProductSearchData[]): ProductSearchResult[] {
	return rawData.map((item) => ({
		productId: String(item.productId ?? ""),
		productName: String(item.productName ?? ""),
		janCode: String(item.janCode ?? ""),
		price: Number(item.price ?? 0),
	}));
}

/** エラーオブジェクトからメッセージを取得する */
function getErrorMessage(err: unknown, fallback: string): string {
	return err instanceof Error ? err.message : fallback;
}

/**
 * 商品検索と表記ゆれ辞書登録を管理するフック.
 *
 * 手動修正時の商品検索と、誤認識の修正データを辞書APIに登録する。
 */
export function useProductSearch(options: UseProductSearchOptions = {}): UseProductSearchReturn {
	const { apiBaseUrl = DEFAULT_API_BASE_URL, debounceMs = DEFAULT_DEBOUNCE_MS } = options;

	const [searchResults, setSearchResults] = useState<readonly ProductSearchResult[]>([]);
	const [isSearching, setIsSearching] = useState(false);
	const [searchError, setSearchError] = useState<string | null>(null);
	const [isRegistering, setIsRegistering] = useState(false);

	const debounceTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
	const abortControllerRef = useRef<AbortController | null>(null);

	const cancelPending = useCallback(() => {
		if (debounceTimerRef.current) {
			clearTimeout(debounceTimerRef.current);
		}
		if (abortControllerRef.current) {
			abortControllerRef.current.abort();
		}
	}, []);

	const fetchProducts = useCallback(
		async (query: string, signal: AbortSignal): Promise<void> => {
			const response = await fetch(`${apiBaseUrl}/products/search?q=${encodeURIComponent(query)}`, {
				signal,
				headers: { Accept: "application/json" },
			});

			if (!response.ok) {
				throw new Error(`検索に失敗しました (${String(response.status)})`);
			}

			const rawData = (await response.json()) as readonly RawProductSearchData[];
			setSearchResults(parseSearchResults(rawData));
		},
		[apiBaseUrl],
	);

	const searchProducts = useCallback(
		async (query: string): Promise<void> => {
			cancelPending();

			if (query.trim().length === 0) {
				setSearchResults([]);
				setSearchError(null);
				return;
			}

			await new Promise<void>((resolve) => {
				debounceTimerRef.current = setTimeout(resolve, debounceMs);
			});

			setIsSearching(true);
			setSearchError(null);

			const controller = new AbortController();
			abortControllerRef.current = controller;

			try {
				await fetchProducts(query, controller.signal);
			} catch (err: unknown) {
				if (err instanceof DOMException && err.name === "AbortError") {
					return;
				}
				setSearchError(getErrorMessage(err, "商品検索に失敗しました"));
				setSearchResults([]);
			} finally {
				setIsSearching(false);
			}
		},
		[cancelPending, fetchProducts, debounceMs],
	);

	const registerAlias = useCallback(
		async (registration: AliasRegistration): Promise<AliasRegistrationResponse> => {
			setIsRegistering(true);

			try {
				const response = await fetch(`${apiBaseUrl}/aliases`, {
					method: "POST",
					headers: {
						"Content-Type": "application/json",
						Accept: "application/json",
					},
					body: JSON.stringify({
						spokenForm: registration.spokenForm,
						productId: registration.productId,
						productName: registration.productName,
					}),
				});

				if (!response.ok) {
					throw new Error(`辞書登録に失敗しました (${String(response.status)})`);
				}

				const data = (await response.json()) as { success?: unknown; message?: unknown };
				return {
					success: Boolean(data.success),
					message: String(data.message ?? "登録完了"),
				};
			} catch (err: unknown) {
				return {
					success: false,
					message: getErrorMessage(err, "辞書登録に失敗しました"),
				};
			} finally {
				setIsRegistering(false);
			}
		},
		[apiBaseUrl],
	);

	const clearSearch = useCallback(() => {
		cancelPending();
		setSearchResults([]);
		setSearchError(null);
		setIsSearching(false);
	}, [cancelPending]);

	return {
		searchResults,
		isSearching,
		searchError,
		isRegistering,
		searchProducts,
		registerAlias,
		clearSearch,
	};
}
