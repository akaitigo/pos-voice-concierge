import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { TranscriptDisplay } from "./TranscriptDisplay";

describe("TranscriptDisplay", () => {
	it("renders transcript text", () => {
		render(
			<TranscriptDisplay result={{ transcript: "コカコーラ 2本", confidence: 0.95, isFinal: true, matches: [] }} />,
		);

		expect(screen.getByText("コカコーラ 2本")).toBeDefined();
	});

	it("renders confidence percentage", () => {
		render(<TranscriptDisplay result={{ transcript: "テスト", confidence: 0.85, isFinal: true, matches: [] }} />);

		expect(screen.getByText("信頼度:")).toBeDefined();
		const allValues = screen.getAllByText("85%");
		expect(allValues.length).toBeGreaterThanOrEqual(1);
	});

	it("does not render confidence when zero", () => {
		render(<TranscriptDisplay result={{ transcript: "テスト", confidence: 0, isFinal: true, matches: [] }} />);

		expect(screen.queryByText("信頼度:")).toBeNull();
	});

	it("shows interim label when not final", () => {
		render(<TranscriptDisplay result={{ transcript: "コカ...", confidence: 0.5, isFinal: false, matches: [] }} />);

		expect(screen.getByText("認識中...")).toBeDefined();
	});

	it("does not show interim label when final", () => {
		render(<TranscriptDisplay result={{ transcript: "コカコーラ", confidence: 0.95, isFinal: true, matches: [] }} />);

		expect(screen.queryByText("認識中...")).toBeNull();
	});

	it("applies interim CSS class when not final", () => {
		const { container } = render(
			<TranscriptDisplay result={{ transcript: "コカ...", confidence: 0.5, isFinal: false, matches: [] }} />,
		);

		const interimText = container.querySelector(".transcript-display__text--interim");
		expect(interimText).not.toBeNull();
	});

	it("has output element for live region", () => {
		const { container } = render(
			<TranscriptDisplay result={{ transcript: "テスト", confidence: 0.9, isFinal: true, matches: [] }} />,
		);

		const output = container.querySelector("output");
		expect(output).not.toBeNull();
	});

	it("renders confidence progress element with correct attributes", () => {
		const { container } = render(
			<TranscriptDisplay result={{ transcript: "テスト", confidence: 0.75, isFinal: true, matches: [] }} />,
		);

		const progress = container.querySelector("progress");
		expect(progress).not.toBeNull();
		expect(progress?.getAttribute("value")).toBe("75");
		expect(progress?.getAttribute("max")).toBe("100");
		expect(progress?.getAttribute("aria-label")).toBe("信頼度 75%");
	});
});
