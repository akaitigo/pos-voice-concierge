import { act, renderHook, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { useQuery } from "./useQuery";

describe("useQuery", () => {
	const mockFetchResponse = (data: Record<string, unknown>, ok = true) => {
		return vi.fn().mockResolvedValue({
			ok,
			status: ok ? 200 : 500,
			json: () => Promise.resolve(data),
		});
	};

	beforeEach(() => {
		vi.restoreAllMocks();
	});

	afterEach(() => {
		vi.restoreAllMocks();
	});

	it("should initialize with null state", () => {
		const { result } = renderHook(() => useQuery());
		expect(result.current.queryResult).toBeNull();
		expect(result.current.isQuerying).toBe(false);
		expect(result.current.queryError).toBeNull();
	});

	it("should skip empty text", async () => {
		const fetchMock = vi.fn();
		global.fetch = fetchMock;

		const { result } = renderHook(() => useQuery());

		await act(async () => {
			await result.current.executeQuery("");
		});

		expect(fetchMock).not.toHaveBeenCalled();
	});

	it("should execute query and return result", async () => {
		const responseData = {
			totalAmount: 50000,
			periodLabel: "今日",
			itemCount: 10,
		};
		global.fetch = mockFetchResponse(responseData);

		const { result } = renderHook(() => useQuery());

		await act(async () => {
			await result.current.executeQuery("今日の売上は？");
		});

		await waitFor(() => {
			expect(result.current.queryResult).not.toBeNull();
		});

		expect(result.current.queryResult?.responseText).toContain("50,000");
		expect(result.current.isQuerying).toBe(false);
	});

	it("should handle error response", async () => {
		global.fetch = vi.fn().mockResolvedValue({
			ok: false,
			status: 500,
		});

		const { result } = renderHook(() => useQuery());

		await act(async () => {
			await result.current.executeQuery("今日の売上は？");
		});

		await waitFor(() => {
			expect(result.current.queryError).not.toBeNull();
		});
	});

	it("should clear query results", async () => {
		const responseData = {
			totalAmount: 50000,
			periodLabel: "今日",
			itemCount: 10,
		};
		global.fetch = mockFetchResponse(responseData);

		const { result } = renderHook(() => useQuery());

		await act(async () => {
			await result.current.executeQuery("今日の売上は？");
		});

		await waitFor(() => {
			expect(result.current.queryResult).not.toBeNull();
		});

		act(() => {
			result.current.clearQuery();
		});

		expect(result.current.queryResult).toBeNull();
		expect(result.current.queryError).toBeNull();
	});

	it("should generate inventory response text", async () => {
		const responseData = {
			productName: "コーラ",
			stockQuantity: 24,
		};
		global.fetch = mockFetchResponse(responseData);

		const { result } = renderHook(() => useQuery());

		await act(async () => {
			await result.current.executeQuery("コーラの在庫は？");
		});

		await waitFor(() => {
			expect(result.current.queryResult).not.toBeNull();
		});

		expect(result.current.queryResult?.responseText).toContain("コーラ");
		expect(result.current.queryResult?.responseText).toContain("24");
	});
});
