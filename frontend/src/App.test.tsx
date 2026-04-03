import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { App } from "./App";
import type { UseVoiceReturn } from "./hooks/useVoice";

const mockStartListening = vi.fn().mockResolvedValue(undefined);
const mockStopListening = vi.fn();

let mockVoiceReturn: UseVoiceReturn;

vi.mock("./hooks/useVoice", () => ({
	useVoice: () => mockVoiceReturn,
}));

describe("App", () => {
	beforeEach(() => {
		mockStartListening.mockClear();
		mockStopListening.mockClear();
		mockVoiceReturn = {
			state: "idle",
			result: null,
			error: null,
			startListening: mockStartListening,
			stopListening: mockStopListening,
		};
	});

	it("renders the heading", () => {
		render(<App />);
		expect(screen.getByRole("heading", { name: "POS Voice Concierge" })).toBeDefined();
	});

	it("renders mic button in idle state", () => {
		render(<App />);
		const button = screen.getByRole("button", { name: "音声入力開始" });
		expect(button).toBeDefined();
	});

	it("calls startListening when mic button is clicked in idle state", async () => {
		const user = userEvent.setup();
		render(<App />);
		const button = screen.getByRole("button", { name: "音声入力開始" });
		await user.click(button);
		expect(mockStartListening).toHaveBeenCalledOnce();
	});

	it("shows stop button in listening state", () => {
		mockVoiceReturn = { ...mockVoiceReturn, state: "listening" };
		render(<App />);
		expect(screen.getByRole("button", { name: "停止" })).toBeDefined();
	});

	it("calls stopListening when stop button is clicked", async () => {
		const user = userEvent.setup();
		mockVoiceReturn = { ...mockVoiceReturn, state: "listening" };
		render(<App />);
		const button = screen.getByRole("button", { name: "停止" });
		await user.click(button);
		expect(mockStopListening).toHaveBeenCalledOnce();
	});

	it("shows processing state", () => {
		mockVoiceReturn = { ...mockVoiceReturn, state: "processing" };
		render(<App />);
		expect(screen.getByRole("button", { name: "停止" })).toBeDefined();
	});

	it("shows error message when error occurs", () => {
		mockVoiceReturn = {
			...mockVoiceReturn,
			state: "error",
			error: "マイクへのアクセスに失敗しました",
		};
		render(<App />);
		expect(screen.getByRole("alert")).toBeDefined();
		expect(screen.getByText("マイクへのアクセスに失敗しました")).toBeDefined();
	});

	it("shows recognition result with transcript", () => {
		mockVoiceReturn = {
			...mockVoiceReturn,
			state: "listening",
			result: {
				transcript: "コカコーラ 2本",
				confidence: 0.95,
				isFinal: false,
				matches: [
					{
						productId: "P001",
						productName: "コカ・コーラ 500ml",
						score: 92.5,
						quantity: 1,
					},
				],
			},
		};
		render(<App />);
		expect(screen.getByText("認識結果: コカコーラ 2本")).toBeDefined();
		expect(screen.getByText("信頼度: 95%")).toBeDefined();
		expect(screen.getByText(/コカ・コーラ 500ml/)).toBeDefined();
	});

	it("shows retry button in error state", async () => {
		const user = userEvent.setup();
		mockVoiceReturn = {
			...mockVoiceReturn,
			state: "error",
			error: "エラー",
		};
		render(<App />);
		const button = screen.getByRole("button", { name: "音声入力開始" });
		await user.click(button);
		expect(mockStartListening).toHaveBeenCalledOnce();
	});
});
