import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { MicButton } from "./MicButton";

describe("MicButton", () => {
	it("renders idle state with mic label", () => {
		render(<MicButton state="idle" onClick={vi.fn()} />);

		const button = screen.getByRole("button", { name: "音声入力開始" });
		expect(button).toBeDefined();
		expect(button.textContent).toContain("音声入力");
	});

	it("renders listening state with stop label", () => {
		render(<MicButton state="listening" onClick={vi.fn()} />);

		const button = screen.getByRole("button", { name: "停止" });
		expect(button).toBeDefined();
		expect(button.textContent).toContain("録音中...");
	});

	it("renders processing state and is disabled", () => {
		render(<MicButton state="processing" onClick={vi.fn()} />);

		const button = screen.getByRole("button", { name: "停止" });
		expect(button).toBeDefined();
		expect((button as HTMLButtonElement).disabled).toBe(true);
		expect(button.textContent).toContain("処理中...");
	});

	it("renders error state with retry label", () => {
		render(<MicButton state="error" onClick={vi.fn()} />);

		const button = screen.getByRole("button", { name: "音声入力開始" });
		expect(button).toBeDefined();
		expect(button.textContent).toContain("再試行");
	});

	it("calls onClick when clicked in idle state", async () => {
		const user = userEvent.setup();
		const onClick = vi.fn();
		render(<MicButton state="idle" onClick={onClick} />);

		await user.click(screen.getByRole("button"));
		expect(onClick).toHaveBeenCalledOnce();
	});

	it("calls onClick when clicked in listening state", async () => {
		const user = userEvent.setup();
		const onClick = vi.fn();
		render(<MicButton state="listening" onClick={onClick} />);

		await user.click(screen.getByRole("button"));
		expect(onClick).toHaveBeenCalledOnce();
	});

	it("does not call onClick when processing", async () => {
		const user = userEvent.setup();
		const onClick = vi.fn();
		render(<MicButton state="processing" onClick={onClick} />);

		await user.click(screen.getByRole("button"));
		expect(onClick).not.toHaveBeenCalled();
	});

	it("shows pulse animation in listening state", () => {
		const { container } = render(<MicButton state="listening" onClick={vi.fn()} />);

		const pulse = container.querySelector(".mic-button__pulse");
		expect(pulse).not.toBeNull();
	});

	it("does not show pulse animation in idle state", () => {
		const { container } = render(<MicButton state="idle" onClick={vi.fn()} />);

		const pulse = container.querySelector(".mic-button__pulse");
		expect(pulse).toBeNull();
	});

	it("has correct CSS class for state", () => {
		const { container } = render(<MicButton state="listening" onClick={vi.fn()} />);

		const button = container.querySelector(".mic-button--listening");
		expect(button).not.toBeNull();
	});
});
