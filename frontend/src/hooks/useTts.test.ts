import { act, renderHook } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { useTts } from "./useTts";

describe("useTts", () => {
	let mockUtterance: {
		lang: string;
		rate: number;
		onstart: (() => void) | null;
		onend: (() => void) | null;
		onerror: (() => void) | null;
	};

	const mockSpeak = vi.fn();
	const mockCancel = vi.fn();

	beforeEach(() => {
		vi.clearAllMocks();

		mockUtterance = {
			lang: "",
			rate: 1,
			onstart: null,
			onend: null,
			onerror: null,
		};

		vi.stubGlobal(
			"SpeechSynthesisUtterance",
			vi.fn(() => mockUtterance),
		);

		Object.defineProperty(window, "speechSynthesis", {
			value: {
				speak: mockSpeak,
				cancel: mockCancel,
			},
			writable: true,
			configurable: true,
		});
	});

	it("starts in idle state", () => {
		const { result } = renderHook(() => useTts());

		expect(result.current.ttsState).toBe("idle");
	});

	it("calls speechSynthesis.speak with correct parameters", () => {
		const { result } = renderHook(() => useTts());

		act(() => {
			result.current.speak("テスト");
		});

		expect(mockCancel).toHaveBeenCalledOnce();
		expect(mockSpeak).toHaveBeenCalledOnce();
		expect(mockUtterance.lang).toBe("ja-JP");
		expect(mockUtterance.rate).toBe(1);
	});

	it("transitions to speaking state on start", () => {
		const { result } = renderHook(() => useTts());

		act(() => {
			result.current.speak("テスト");
		});

		act(() => {
			mockUtterance.onstart?.();
		});

		expect(result.current.ttsState).toBe("speaking");
	});

	it("transitions back to idle on end", () => {
		const { result } = renderHook(() => useTts());

		act(() => {
			result.current.speak("テスト");
		});

		act(() => {
			mockUtterance.onstart?.();
		});

		act(() => {
			mockUtterance.onend?.();
		});

		expect(result.current.ttsState).toBe("idle");
	});

	it("transitions to idle on error", () => {
		const { result } = renderHook(() => useTts());

		act(() => {
			result.current.speak("テスト");
		});

		act(() => {
			mockUtterance.onstart?.();
		});

		act(() => {
			mockUtterance.onerror?.();
		});

		expect(result.current.ttsState).toBe("idle");
	});

	it("cancels speech when cancelSpeech is called", () => {
		const { result } = renderHook(() => useTts());

		act(() => {
			result.current.speak("テスト");
		});

		act(() => {
			result.current.cancelSpeech();
		});

		expect(mockCancel).toHaveBeenCalledTimes(2);
		expect(result.current.ttsState).toBe("idle");
	});

	it("uses custom language and rate", () => {
		const { result } = renderHook(() => useTts({ lang: "en-US", rate: 1.5 }));

		act(() => {
			result.current.speak("test");
		});

		expect(mockUtterance.lang).toBe("en-US");
		expect(mockUtterance.rate).toBe(1.5);
	});
});
