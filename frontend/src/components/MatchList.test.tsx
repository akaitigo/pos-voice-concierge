import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import type { ProductMatch } from "../types";
import { MatchList } from "./MatchList";

const sampleMatches: ProductMatch[] = [
	{ productId: "P001", productName: "コカ・コーラ 500ml", score: 95, quantity: 2 },
	{ productId: "P002", productName: "コカ・コーラ 350ml", score: 88, quantity: 1 },
	{ productId: "P003", productName: "コカ・コーラ ゼロ 500ml", score: 82, quantity: 1 },
];

describe("MatchList", () => {
	it("renders empty message when no matches", () => {
		render(<MatchList matches={[]} onSelect={vi.fn()} selectedProductId={null} />);

		expect(screen.getByText("マッチする商品が見つかりませんでした")).toBeDefined();
	});

	it("renders all match candidates", () => {
		render(<MatchList matches={sampleMatches} onSelect={vi.fn()} selectedProductId={null} />);

		expect(screen.getByText("コカ・コーラ 500ml")).toBeDefined();
		expect(screen.getByText("コカ・コーラ 350ml")).toBeDefined();
		expect(screen.getByText("コカ・コーラ ゼロ 500ml")).toBeDefined();
	});

	it("displays scores for each match", () => {
		render(<MatchList matches={sampleMatches} onSelect={vi.fn()} selectedProductId={null} />);

		expect(screen.getByText("スコア: 95%")).toBeDefined();
		expect(screen.getByText("スコア: 88%")).toBeDefined();
		expect(screen.getByText("スコア: 82%")).toBeDefined();
	});

	it("displays quantity when greater than zero", () => {
		render(<MatchList matches={sampleMatches} onSelect={vi.fn()} selectedProductId={null} />);

		expect(screen.getByText("数量: 2")).toBeDefined();
	});

	it("calls onSelect when a candidate is clicked", async () => {
		const user = userEvent.setup();
		const onSelect = vi.fn();
		render(<MatchList matches={sampleMatches} onSelect={onSelect} selectedProductId={null} />);

		await user.click(screen.getByText("コカ・コーラ 500ml"));

		expect(onSelect).toHaveBeenCalledOnce();
		expect(onSelect).toHaveBeenCalledWith(sampleMatches[0]);
	});

	it("highlights selected product", () => {
		const { container } = render(<MatchList matches={sampleMatches} onSelect={vi.fn()} selectedProductId="P001" />);

		const selectedItem = container.querySelector(".match-list__item--selected");
		expect(selectedItem).not.toBeNull();
	});

	it("marks selected button with aria-pressed", () => {
		render(<MatchList matches={sampleMatches} onSelect={vi.fn()} selectedProductId="P001" />);

		const buttons = screen.getAllByRole("button");
		expect(buttons[0]?.getAttribute("aria-pressed")).toBe("true");
		expect(buttons[1]?.getAttribute("aria-pressed")).toBe("false");
	});

	it("has candidates container with aria-label", () => {
		const { container } = render(<MatchList matches={sampleMatches} onSelect={vi.fn()} selectedProductId={null} />);

		const items = container.querySelector('[aria-label="商品候補リスト"]');
		expect(items).not.toBeNull();
	});

	it("provides accessible label for each candidate button", () => {
		render(<MatchList matches={sampleMatches} onSelect={vi.fn()} selectedProductId={null} />);

		expect(screen.getByLabelText("コカ・コーラ 500ml を選択 (スコア: 95%)")).toBeDefined();
	});
});
