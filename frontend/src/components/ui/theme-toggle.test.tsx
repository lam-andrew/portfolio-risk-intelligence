import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { ThemeToggle } from "./theme-toggle";
afterEach(() => {
  vi.restoreAllMocks();
  localStorage.removeItem("orbit-theme");
  document.documentElement.classList.remove("dark");
});
it("switches the application theme and remembers the preference", () => {
  document.documentElement.classList.add("dark");
  render(<ThemeToggle />);
  fireEvent.click(screen.getByRole("button", { name: "Switch to light mode" }));
  expect(document.documentElement).not.toHaveClass("dark");
  expect(localStorage.getItem("orbit-theme")).toBe("light");
  fireEvent.click(screen.getByRole("button", { name: "Switch to dark mode" }));
  expect(document.documentElement).toHaveClass("dark");
});
it("still switches appearance when local storage is blocked", () => {
  vi.spyOn(Storage.prototype, "setItem").mockImplementation(() => {
    throw new Error("blocked");
  });
  render(<ThemeToggle />);
  fireEvent.click(screen.getByRole("button", { name: "Switch to dark mode" }));
  expect(document.documentElement).toHaveClass("dark");
});
