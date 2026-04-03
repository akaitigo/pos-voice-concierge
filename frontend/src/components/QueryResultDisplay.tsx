import type { QueryResult } from "../types";

interface QueryResultDisplayProps {
	readonly result: QueryResult;
}

/** 売上データの形状 */
interface SalesDataShape {
	readonly totalAmount: number;
	readonly itemCount?: number;
}

/** 在庫データの形状 */
interface InventoryDataShape {
	readonly stockQuantity: number;
}

/** トップ商品エントリの形状 */
interface TopProductEntryShape {
	readonly rank: number;
	readonly productName: string;
	readonly totalAmount: number;
	readonly quantitySold: number;
}

/** トップ商品データの形状 */
interface TopProductsDataShape {
	readonly entries: readonly TopProductEntryShape[];
}

/**
 * クエリ結果表示コンポーネント.
 *
 * 売上照会・在庫照会・トップ商品の結果を表示する。
 */
export function QueryResultDisplay({ result }: QueryResultDisplayProps): React.JSX.Element {
	return (
		<output className="query-result" aria-live="polite">
			<h2 className="query-result__heading">クエリ結果</h2>
			<p className="query-result__intent">
				種別: <span className="query-result__intent-value">{formatIntent(result.intent)}</span>
			</p>
			<p className="query-result__response-text">{result.responseText}</p>
			{renderDataDetails(result)}
		</output>
	);
}

function formatIntent(intent: string): string {
	const labels: Record<string, string> = {
		sales_inquiry: "売上照会",
		inventory_inquiry: "在庫照会",
		top_products: "売上トップ",
		product_registration: "商品登録",
		unknown: "不明",
	};
	return labels[intent] ?? intent;
}

function asSalesData(data: Record<string, unknown>): SalesDataShape | null {
	if (!("totalAmount" in data)) {
		return null;
	}
	const typed = data as unknown as SalesDataShape;
	return { totalAmount: Number(typed.totalAmount), itemCount: Number(typed.itemCount ?? 0) };
}

function asInventoryData(data: Record<string, unknown>): InventoryDataShape | null {
	if (!("stockQuantity" in data)) {
		return null;
	}
	const typed = data as unknown as InventoryDataShape;
	return { stockQuantity: Number(typed.stockQuantity) };
}

function asTopProductsData(data: Record<string, unknown>): TopProductsDataShape | null {
	if (!("entries" in data)) {
		return null;
	}
	const typed = data as unknown as { entries: unknown };
	if (!Array.isArray(typed.entries)) {
		return null;
	}
	const rawEntries = typed.entries as readonly Record<string, unknown>[];
	return {
		entries: rawEntries.map((e) => {
			const entry = e as unknown as TopProductEntryShape;
			return {
				rank: Number(entry.rank),
				productName: String(entry.productName),
				totalAmount: Number(entry.totalAmount),
				quantitySold: Number(entry.quantitySold),
			};
		}),
	};
}

function renderDataDetails(result: QueryResult): React.JSX.Element | null {
	const { data } = result;

	const salesData = asSalesData(data);
	if (salesData) {
		const amount = salesData.totalAmount.toLocaleString();
		return (
			<div className="query-result__details">
				<p className="query-result__amount">
					売上合計: <strong>&yen;{amount}</strong>
				</p>
				{salesData.itemCount !== undefined && salesData.itemCount > 0 && (
					<p className="query-result__item-count">取引件数: {salesData.itemCount}件</p>
				)}
			</div>
		);
	}

	const inventoryData = asInventoryData(data);
	if (inventoryData) {
		return (
			<div className="query-result__details">
				<p className="query-result__stock">
					在庫数: <strong>{inventoryData.stockQuantity}個</strong>
				</p>
			</div>
		);
	}

	const topData = asTopProductsData(data);
	if (topData) {
		return (
			<div className="query-result__details">
				<table className="query-result__table">
					<thead>
						<tr>
							<th>順位</th>
							<th>商品名</th>
							<th>売上</th>
							<th>販売数</th>
						</tr>
					</thead>
					<tbody>
						{topData.entries.map((entry) => (
							<tr key={entry.rank}>
								<td>{entry.rank}</td>
								<td>{entry.productName}</td>
								<td>&yen;{entry.totalAmount.toLocaleString()}</td>
								<td>{entry.quantitySold}個</td>
							</tr>
						))}
					</tbody>
				</table>
			</div>
		);
	}

	return null;
}
