import { act, renderHook } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { useProductSearch } from "./useProductSearch";

describe("useProductSearch", () => {
	const mockFetch = vi.fn();

	beforeEach(() => {
		vi.clearAllMocks();
		vi.useFakeTimers();
		vi.stubGlobal("fetch", mockFetch);
	});

	afterEach(() => {
		vi.useRealTimers();
	});

	it("starts with empty results", () => {
		const { result } = renderHook(() => useProductSearch());

		expect(result.current.searchResults).toEqual([]);
		expect(result.current.isSearching).toBe(false);
		expect(result.current.searchError).toBeNull();
		expect(result.current.isRegistering).toBe(false);
	});

	it("clears results when search query is empty", async () => {
		const { result } = renderHook(() => useProductSearch());

		await act(async () => {
			await result.current.searchProducts("");
		});

		expect(result.current.searchResults).toEqual([]);
		expect(mockFetch).not.toHaveBeenCalled();
	});

	it("searches products after debounce", async () => {
		mockFetch.mockResolvedValueOnce({
			ok: true,
			json: async () => [
				{
					productId: "P001",
					productName: "コカ・コーラ 500ml",
					janCode: "4902102000001",
					price: 150,
				},
			],
		});

		const { result } = renderHook(() => useProductSearch({ debounceMs: 100 }));

		const searchPromise = act(async () => {
			const p = result.current.searchProducts("コカ");
			vi.advanceTimersByTime(100);
			await p;
		});

		await searchPromise;

		expect(mockFetch).toHaveBeenCalledOnce();
		expect(result.current.searchResults).toHaveLength(1);
		expect(result.current.searchResults[0]?.productName).toBe("コカ・コーラ 500ml");
	});

	it("handles search API error", async () => {
		mockFetch.mockResolvedValueOnce({
			ok: false,
			status: 500,
		});

		const { result } = renderHook(() => useProductSearch({ debounceMs: 0 }));

		await act(async () => {
			const p = result.current.searchProducts("コカ");
			vi.advanceTimersByTime(0);
			await p;
		});

		expect(result.current.searchError).toBe("検索に失敗しました (500)");
		expect(result.current.searchResults).toEqual([]);
	});

	it("registers alias successfully", async () => {
		mockFetch.mockResolvedValueOnce({
			ok: true,
			json: async () => ({
				success: true,
				message: "登録完了",
			}),
		});

		const { result } = renderHook(() => useProductSearch());

		let response: { success: boolean; message: string } | undefined;
		await act(async () => {
			response = await result.current.registerAlias({
				spokenForm: "コカコーラ",
				productId: "P001",
				productName: "コカ・コーラ 500ml",
			});
		});

		expect(mockFetch).toHaveBeenCalledWith("/api/aliases", expect.objectContaining({ method: "POST" }));
		expect(response?.success).toBe(true);
	});

	it("handles alias registration failure", async () => {
		mockFetch.mockResolvedValueOnce({
			ok: false,
			status: 500,
		});

		const { result } = renderHook(() => useProductSearch());

		let response: { success: boolean; message: string } | undefined;
		await act(async () => {
			response = await result.current.registerAlias({
				spokenForm: "コカコーラ",
				productId: "P001",
				productName: "コカ・コーラ 500ml",
			});
		});

		expect(response?.success).toBe(false);
		expect(response?.message).toBe("辞書登録に失敗しました (500)");
	});

	it("clears search results", () => {
		const { result } = renderHook(() => useProductSearch());

		act(() => {
			result.current.clearSearch();
		});

		expect(result.current.searchResults).toEqual([]);
		expect(result.current.searchError).toBeNull();
		expect(result.current.isSearching).toBe(false);
	});
});
