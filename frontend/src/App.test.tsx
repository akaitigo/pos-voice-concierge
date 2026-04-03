import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";
import { App } from "./App";

describe("App", () => {
	it("renders the heading", () => {
		render(<App />);
		expect(screen.getByRole("heading", { name: "POS Voice Concierge" })).toBeDefined();
	});

	it("renders mic button in idle state", () => {
		render(<App />);
		const button = screen.getByRole("button", { name: "音声入力開始" });
		expect(button).toBeDefined();
	});

	it("toggles to listening state on click", async () => {
		const user = userEvent.setup();
		render(<App />);
		const button = screen.getByRole("button", { name: "音声入力開始" });
		await user.click(button);
		expect(screen.getByRole("button", { name: "停止" })).toBeDefined();
	});

	it("toggles back to idle on second click", async () => {
		const user = userEvent.setup();
		render(<App />);
		const button = screen.getByRole("button", { name: "音声入力開始" });
		await user.click(button);
		const stopButton = screen.getByRole("button", { name: "停止" });
		await user.click(stopButton);
		expect(screen.getByRole("button", { name: "音声入力開始" })).toBeDefined();
	});
});
