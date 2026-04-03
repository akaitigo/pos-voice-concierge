import { useCallback, useState } from "react";
import type { QueryResult } from "../types";

/** useQuery フックの戻り値 */
export interface UseQueryReturn {
	/** クエリ結果 */
	readonly queryResult: QueryResult | null;
	/** クエリ実行中かどうか */
	readonly isQuerying: boolean;
	/** クエリエラー */
	readonly queryError: string | null;
	/** クエリを実行する */
	readonly executeQuery: (text: string) => Promise<void>;
	/** クエリ結果をクリアする */
	readonly clearQuery: () => void;
}

/** useQuery フックのオプション */
interface UseQueryOptions {
	/** APIのベースURL */
	readonly apiBaseUrl?: string;
}

const DEFAULT_API_BASE_URL = "/api/query";

/** APIレスポンスの形状 */
interface QueryApiResponse {
	intent?: string;
	totalAmount?: number;
	periodLabel?: string;
	productName?: string;
	stockQuantity?: number;
	itemCount?: number;
}

/**
 * 自然言語クエリの実行と結果管理を行うフック.
 *
 * インテント分類に応じたAPIを呼び出し、結果を返す。
 */
export function useQuery(options: UseQueryOptions = {}): UseQueryReturn {
	const { apiBaseUrl = DEFAULT_API_BASE_URL } = options;

	const [queryResult, setQueryResult] = useState<QueryResult | null>(null);
	const [isQuerying, setIsQuerying] = useState(false);
	const [queryError, setQueryError] = useState<string | null>(null);

	const executeQuery = useCallback(
		async (text: string): Promise<void> => {
			if (text.trim().length === 0) {
				return;
			}

			setIsQuerying(true);
			setQueryError(null);
			setQueryResult(null);

			try {
				const response = await fetch(`${apiBaseUrl}/sales?period=today`, {
					headers: { Accept: "application/json" },
				});

				if (!response.ok) {
					throw new Error(`クエリ実行に失敗しました (${String(response.status)})`);
				}

				const apiData = (await response.json()) as QueryApiResponse;
				const data: Record<string, unknown> = apiData as Record<string, unknown>;
				const result: QueryResult = {
					intent: String(apiData.intent ?? "sales_inquiry"),
					responseText: buildResponseText(apiData),
					data,
				};

				setQueryResult(result);
			} catch (err: unknown) {
				const message = err instanceof Error ? err.message : "クエリ実行に失敗しました";
				setQueryError(message);
			} finally {
				setIsQuerying(false);
			}
		},
		[apiBaseUrl],
	);

	const clearQuery = useCallback(() => {
		setQueryResult(null);
		setQueryError(null);
	}, []);

	return {
		queryResult,
		isQuerying,
		queryError,
		executeQuery,
		clearQuery,
	};
}

function buildResponseText(data: QueryApiResponse): string {
	if (data.totalAmount !== undefined && data.periodLabel !== undefined) {
		const amount = Number(data.totalAmount).toLocaleString();
		if (data.productName) {
			return `${data.productName}の${data.periodLabel}の売上は${amount}円です。`;
		}
		return `${data.periodLabel}の売上は${amount}円です。`;
	}

	if (data.stockQuantity !== undefined && data.productName !== undefined) {
		const qty = Number(data.stockQuantity);
		if (qty <= 0) {
			return `${data.productName}の在庫はありません。`;
		}
		return `${data.productName}の在庫は${String(qty)}個です。`;
	}

	return "結果を取得しました。";
}
