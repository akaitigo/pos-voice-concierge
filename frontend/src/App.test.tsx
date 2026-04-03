import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { App } from "./App";
import type { UseProductSearchReturn } from "./hooks/useProductSearch";
import type { UseTtsReturn } from "./hooks/useTts";
import type { UseVoiceReturn } from "./hooks/useVoice";

const mockStartListening = vi.fn().mockResolvedValue(undefined);
const mockStopListening = vi.fn();
const mockSpeak = vi.fn();
const mockCancelSpeech = vi.fn();
const mockSearchProducts = vi.fn().mockResolvedValue(undefined);
const mockRegisterAlias = vi.fn().mockResolvedValue({ success: true, message: "登録完了" });
const mockClearSearch = vi.fn();

let mockVoiceReturn: UseVoiceReturn;
let mockTtsReturn: UseTtsReturn;
let mockProductSearchReturn: UseProductSearchReturn;

vi.mock("./hooks/useVoice", () => ({
	useVoice: () => mockVoiceReturn,
}));

vi.mock("./hooks/useTts", () => ({
	useTts: () => mockTtsReturn,
}));

vi.mock("./hooks/useProductSearch", () => ({
	useProductSearch: () => mockProductSearchReturn,
}));

describe("App", () => {
	beforeEach(() => {
		vi.clearAllMocks();
		mockVoiceReturn = {
			state: "idle",
			result: null,
			error: null,
			startListening: mockStartListening,
			stopListening: mockStopListening,
		};
		mockTtsReturn = {
			ttsState: "idle",
			speak: mockSpeak,
			cancelSpeech: mockCancelSpeech,
		};
		mockProductSearchReturn = {
			searchResults: [],
			isSearching: false,
			searchError: null,
			isRegistering: false,
			searchProducts: mockSearchProducts,
			registerAlias: mockRegisterAlias,
			clearSearch: mockClearSearch,
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
		expect(screen.getByText("コカコーラ 2本")).toBeDefined();
		expect(screen.getByText("信頼度:")).toBeDefined();
		expect(screen.getByText("コカ・コーラ 500ml")).toBeDefined();
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

	it("shows match list with candidates", () => {
		mockVoiceReturn = {
			...mockVoiceReturn,
			result: {
				transcript: "コカコーラ",
				confidence: 0.9,
				isFinal: true,
				matches: [
					{ productId: "P001", productName: "コカ・コーラ 500ml", score: 95, quantity: 2 },
					{ productId: "P002", productName: "コカ・コーラ 350ml", score: 88, quantity: 1 },
				],
			},
		};
		render(<App />);
		expect(screen.getByText("商品候補")).toBeDefined();
		expect(screen.getByText("コカ・コーラ 500ml")).toBeDefined();
		expect(screen.getByText("コカ・コーラ 350ml")).toBeDefined();
	});

	it("shows confirmed product when a match is selected", async () => {
		const user = userEvent.setup();
		mockVoiceReturn = {
			...mockVoiceReturn,
			result: {
				transcript: "コカコーラ",
				confidence: 0.9,
				isFinal: true,
				matches: [{ productId: "P001", productName: "コカ・コーラ 500ml", score: 95, quantity: 2 }],
			},
		};
		render(<App />);

		await user.click(screen.getByLabelText("コカ・コーラ 500ml を選択 (スコア: 95%)"));

		expect(screen.getByText("商品確定")).toBeDefined();
		expect(screen.getByText("コカ・コーラ 500ml")).toBeDefined();
		expect(screen.getByText("数量: 2")).toBeDefined();
	});

	it("calls TTS when a match is selected", async () => {
		const user = userEvent.setup();
		mockVoiceReturn = {
			...mockVoiceReturn,
			result: {
				transcript: "コカコーラ",
				confidence: 0.9,
				isFinal: true,
				matches: [{ productId: "P001", productName: "コカ・コーラ 500ml", score: 95, quantity: 2 }],
			},
		};
		render(<App />);

		await user.click(screen.getByLabelText("コカ・コーラ 500ml を選択 (スコア: 95%)"));

		expect(mockSpeak).toHaveBeenCalledWith("コカ・コーラ 500ml、2点で登録しました");
	});

	it("shows manual search button when matches are available", () => {
		mockVoiceReturn = {
			...mockVoiceReturn,
			result: {
				transcript: "コカコーラ",
				confidence: 0.9,
				isFinal: true,
				matches: [{ productId: "P001", productName: "コカ・コーラ 500ml", score: 95, quantity: 2 }],
			},
		};
		render(<App />);

		expect(screen.getByText("正しい商品が見つからない場合はこちら")).toBeDefined();
	});

	it("opens search dialog when manual search button is clicked", async () => {
		const user = userEvent.setup();
		mockVoiceReturn = {
			...mockVoiceReturn,
			result: {
				transcript: "コカコーラ",
				confidence: 0.9,
				isFinal: true,
				matches: [{ productId: "P001", productName: "コカ・コーラ 500ml", score: 95, quantity: 2 }],
			},
		};
		render(<App />);

		await user.click(screen.getByText("正しい商品が見つからない場合はこちら"));

		expect(screen.getByRole("dialog", { name: "商品検索" })).toBeDefined();
	});

	it("shows TTS status when speaking", () => {
		mockTtsReturn = { ...mockTtsReturn, ttsState: "speaking" };
		render(<App />);

		expect(screen.getByText("読み上げ中...")).toBeDefined();
	});

	it("resets state when clear button is clicked", async () => {
		const user = userEvent.setup();
		mockVoiceReturn = {
			...mockVoiceReturn,
			result: {
				transcript: "コカコーラ",
				confidence: 0.9,
				isFinal: true,
				matches: [{ productId: "P001", productName: "コカ・コーラ 500ml", score: 95, quantity: 2 }],
			},
		};
		render(<App />);

		await user.click(screen.getByLabelText("コカ・コーラ 500ml を選択 (スコア: 95%)"));
		expect(screen.getByText("商品確定")).toBeDefined();

		await user.click(screen.getByText("クリア"));
		expect(screen.queryByText("商品確定")).toBeNull();
	});
});
