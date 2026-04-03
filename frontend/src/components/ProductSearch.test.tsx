import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { ProductSearch } from "./ProductSearch";

const defaultProps = {
	originalTranscript: "コカコーラ",
	searchResults: [],
	isSearching: false,
	searchError: null,
	isRegistering: false,
	onSearch: vi.fn().mockResolvedValue(undefined),
	onSelectCorrect: vi.fn(),
	onClose: vi.fn(),
};

describe("ProductSearch", () => {
	it("renders the search dialog", () => {
		render(<ProductSearch {...defaultProps} />);

		expect(screen.getByRole("dialog", { name: "商品検索" })).toBeDefined();
		expect(screen.getByText("商品を手動で検索")).toBeDefined();
	});

	it("shows original transcript", () => {
		render(<ProductSearch {...defaultProps} />);

		expect(screen.getByText("コカコーラ")).toBeDefined();
	});

	it("calls onSearch when typing in search input", async () => {
		const user = userEvent.setup();
		const onSearch = vi.fn().mockResolvedValue(undefined);

		render(<ProductSearch {...defaultProps} onSearch={onSearch} />);

		const input = screen.getByLabelText("商品名検索");
		await user.type(input, "コカ");

		expect(onSearch).toHaveBeenCalled();
	});

	it("renders search results", () => {
		const searchResults = [
			{ productId: "P001", productName: "コカ・コーラ 500ml", janCode: "4902102000001", price: 150 },
			{ productId: "P002", productName: "コカ・コーラ 350ml", janCode: "4902102000002", price: 120 },
		];

		render(<ProductSearch {...defaultProps} searchResults={searchResults} />);

		expect(screen.getByText("コカ・コーラ 500ml")).toBeDefined();
		expect(screen.getByText("コカ・コーラ 350ml")).toBeDefined();
	});

	it("displays JAN code and price in results", () => {
		const searchResults = [
			{ productId: "P001", productName: "コカ・コーラ 500ml", janCode: "4902102000001", price: 150 },
		];

		render(<ProductSearch {...defaultProps} searchResults={searchResults} />);

		expect(screen.getByText("JAN: 4902102000001")).toBeDefined();
	});

	it("calls onSelectCorrect with alias registration when product is selected", async () => {
		const user = userEvent.setup();
		const onSelectCorrect = vi.fn();
		const searchResults = [
			{ productId: "P001", productName: "コカ・コーラ 500ml", janCode: "4902102000001", price: 150 },
		];

		render(<ProductSearch {...defaultProps} searchResults={searchResults} onSelectCorrect={onSelectCorrect} />);

		await user.click(screen.getByLabelText("コカ・コーラ 500ml を正しい商品として選択"));

		expect(onSelectCorrect).toHaveBeenCalledOnce();
		expect(onSelectCorrect).toHaveBeenCalledWith(searchResults[0], {
			spokenForm: "コカコーラ",
			productId: "P001",
			productName: "コカ・コーラ 500ml",
		});
	});

	it("calls onClose when close button is clicked", async () => {
		const user = userEvent.setup();
		const onClose = vi.fn();

		render(<ProductSearch {...defaultProps} onClose={onClose} />);

		await user.click(screen.getByLabelText("検索を閉じる"));

		expect(onClose).toHaveBeenCalledOnce();
	});

	it("shows search error", () => {
		render(<ProductSearch {...defaultProps} searchError="検索に失敗しました" />);

		expect(screen.getByRole("alert")).toBeDefined();
		expect(screen.getByText("検索に失敗しました")).toBeDefined();
	});

	it("shows loading indicator when searching", () => {
		render(<ProductSearch {...defaultProps} isSearching={true} />);

		expect(screen.getByLabelText("検索中")).toBeDefined();
	});

	it("shows registering status", () => {
		render(<ProductSearch {...defaultProps} isRegistering={true} />);

		expect(screen.getByText("辞書に登録中...")).toBeDefined();
	});

	it("disables result buttons when registering", () => {
		const searchResults = [
			{ productId: "P001", productName: "コカ・コーラ 500ml", janCode: "4902102000001", price: 150 },
		];

		render(<ProductSearch {...defaultProps} searchResults={searchResults} isRegistering={true} />);

		const button = screen.getByLabelText("コカ・コーラ 500ml を正しい商品として選択");
		expect((button as HTMLButtonElement).disabled).toBe(true);
	});

	it("shows no results message when search returns empty", async () => {
		const user = userEvent.setup();
		render(<ProductSearch {...defaultProps} />);

		const input = screen.getByLabelText("商品名検索");
		await user.type(input, "存在しない商品");

		expect(screen.getByText("該当する商品が見つかりませんでした")).toBeDefined();
	});
});
