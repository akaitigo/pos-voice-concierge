import { act, renderHook } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { useVoice } from "./useVoice";

// MediaRecorder のモック
class MockMediaRecorder {
	state = "inactive";
	ondataavailable: ((event: { data: Blob }) => void) | null = null;
	start = vi.fn(() => {
		this.state = "recording";
	});
	stop = vi.fn(() => {
		this.state = "inactive";
	});

	static isTypeSupported = vi.fn(() => true);
}

// WebSocket のモック
class MockWebSocket {
	static readonly CONNECTING = 0;
	static readonly OPEN = 1;
	static readonly CLOSING = 2;
	static readonly CLOSED = 3;

	readonly CONNECTING = 0;
	readonly OPEN = 1;
	readonly CLOSING = 2;
	readonly CLOSED = 3;

	readyState = MockWebSocket.OPEN;
	binaryType = "blob";
	onopen: (() => void) | null = null;
	onmessage: ((event: { data: string }) => void) | null = null;
	onerror: (() => void) | null = null;
	onclose: (() => void) | null = null;
	send = vi.fn();
	close = vi.fn(() => {
		this.readyState = MockWebSocket.CLOSED;
	});
}

// navigator.mediaDevices のモック
const mockGetUserMedia = vi.fn();
const mockMediaStream = {
	getTracks: () => [{ stop: vi.fn() }],
};

describe("useVoice", () => {
	let mockWs: MockWebSocket;

	beforeEach(() => {
		vi.clearAllMocks();

		mockGetUserMedia.mockResolvedValue(mockMediaStream);
		Object.defineProperty(globalThis.navigator, "mediaDevices", {
			value: { getUserMedia: mockGetUserMedia },
			writable: true,
			configurable: true,
		});

		vi.stubGlobal("MediaRecorder", MockMediaRecorder);

		mockWs = new MockWebSocket();
		vi.stubGlobal(
			"WebSocket",
			Object.assign(
				vi.fn(() => mockWs),
				{
					CONNECTING: 0,
					OPEN: 1,
					CLOSING: 2,
					CLOSED: 3,
				},
			),
		);
	});

	it("starts in idle state", () => {
		const { result } = renderHook(() => useVoice());

		expect(result.current.state).toBe("idle");
		expect(result.current.result).toBeNull();
		expect(result.current.error).toBeNull();
	});

	it("transitions to listening when startListening is called", async () => {
		const { result } = renderHook(() => useVoice());

		await act(async () => {
			await result.current.startListening();
		});

		// onopen を呼び出してリスニング状態に遷移させる
		act(() => {
			mockWs.onopen?.();
		});

		expect(result.current.state).toBe("listening");
		expect(mockGetUserMedia).toHaveBeenCalledOnce();
	});

	it("transitions back to idle when stopListening is called", async () => {
		const { result } = renderHook(() => useVoice());

		await act(async () => {
			await result.current.startListening();
		});

		act(() => {
			mockWs.onopen?.();
		});

		act(() => {
			result.current.stopListening();
		});

		expect(result.current.state).toBe("idle");
	});

	it("sets error state when getUserMedia fails", async () => {
		mockGetUserMedia.mockRejectedValue(new Error("Permission denied"));
		const { result } = renderHook(() => useVoice());

		await act(async () => {
			await result.current.startListening();
		});

		expect(result.current.state).toBe("error");
		expect(result.current.error).toBe("Permission denied");
	});

	it("processes recognition result from WebSocket message", async () => {
		const { result } = renderHook(() => useVoice());

		await act(async () => {
			await result.current.startListening();
		});

		act(() => {
			mockWs.onopen?.();
		});

		const recognitionJson = JSON.stringify({
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
		});

		act(() => {
			mockWs.onmessage?.({ data: recognitionJson });
		});

		expect(result.current.result).not.toBeNull();
		expect(result.current.result?.transcript).toBe("コカコーラ 2本");
		expect(result.current.result?.confidence).toBe(0.95);
		expect(result.current.result?.matches).toHaveLength(1);
		expect(result.current.result?.matches[0]?.productName).toBe("コカ・コーラ 500ml");
	});

	it("sets error state on WebSocket error", async () => {
		const { result } = renderHook(() => useVoice());

		await act(async () => {
			await result.current.startListening();
		});

		act(() => {
			mockWs.onopen?.();
		});

		act(() => {
			mockWs.onerror?.();
		});

		expect(result.current.state).toBe("error");
		expect(result.current.error).toBe("WebSocket接続エラーが発生しました");
	});
});
