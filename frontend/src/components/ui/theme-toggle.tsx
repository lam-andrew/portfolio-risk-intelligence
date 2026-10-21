import { useSyncExternalStore } from "react";
import { Button } from "./button";

const themeEvent = "orbit-theme-change";
const isDark = () => document.documentElement.classList.contains("dark");

function subscribe(onChange: () => void) {
  window.addEventListener(themeEvent, onChange);
  return () => window.removeEventListener(themeEvent, onChange);
}

export function ThemeToggle() {
  const dark = useSyncExternalStore(subscribe, isDark);
  function toggle() {
    const next = !isDark();
    document.documentElement.classList.toggle("dark", next);
    try {
      localStorage.setItem("orbit-theme", next ? "dark" : "light");
    } catch {
      /* Storage may be unavailable. The current theme still works. */
    }
    window.dispatchEvent(new Event(themeEvent));
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
