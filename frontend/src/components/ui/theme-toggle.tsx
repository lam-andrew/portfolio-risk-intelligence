import { useState } from "react";
import { Button } from "./button";

export function ThemeToggle() {
  const [dark, setDark] = useState(() => document.documentElement.classList.contains("dark"));
  function toggle() {
    const next = !dark;
    document.documentElement.classList.toggle("dark", next);
    try {
      localStorage.setItem("orbit-theme", next ? "dark" : "light");
    } catch {
      /* Storage may be unavailable. The current theme still works. */
    }
    setDark(next);
  }
  return (
    <Button
      variant="outline"
      size="sm"
      onClick={toggle}
      aria-label={`Switch to ${dark ? "light" : "dark"} mode`}
    >
      {dark ? "Light mode" : "Dark mode"}
    </Button>
  );
}
