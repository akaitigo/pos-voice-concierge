import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import type { QueryResult } from "../types";
import { QueryResultDisplay } from "./QueryResultDisplay";

describe("QueryResultDisplay", () => {
	it("should render sales result", () => {
		const result: QueryResult = {
			intent: "sales_inquiry",
			responseText: "今日の売上は50,000円です。",
			data: {
				totalAmount: 50000,
				periodLabel: "今日",
				itemCount: 10,
			},
		};

		render(<QueryResultDisplay result={result} />);

		expect(screen.getByText("クエリ結果")).toBeDefined();
		expect(screen.getByText("売上照会")).toBeDefined();
		expect(screen.getByText("今日の売上は50,000円です。")).toBeDefined();
	});

	it("should render inventory result", () => {
		const result: QueryResult = {
			intent: "inventory_inquiry",
			responseText: "コーラの在庫は24個です。",
			data: {
				productName: "コーラ",
				stockQuantity: 24,
			},
		};

		render(<QueryResultDisplay result={result} />);

		expect(screen.getByText("在庫照会")).toBeDefined();
		expect(screen.getByText("コーラの在庫は24個です。")).toBeDefined();
	});

	it("should render top products result", () => {
		const result: QueryResult = {
			intent: "top_products",
			responseText: "今日の売上トップ2です。",
			data: {
				entries: [
					{ rank: 1, productName: "コーラ", totalAmount: 50000, quantitySold: 100 },
					{ rank: 2, productName: "お茶", totalAmount: 30000, quantitySold: 75 },
				],
				periodLabel: "今日",
			},
		};

		render(<QueryResultDisplay result={result} />);

		expect(screen.getByText("売上トップ")).toBeDefined();
		expect(screen.getByText("コーラ")).toBeDefined();
		expect(screen.getByText("お茶")).toBeDefined();
	});

	it("should render unknown intent", () => {
		const result: QueryResult = {
			intent: "unknown",
			responseText: "質問の意図がわかりませんでした。",
			data: {},
		};

		render(<QueryResultDisplay result={result} />);

		expect(screen.getByText("不明")).toBeDefined();
	});
});
