import { Link, NavLink, useLocation } from "react-router-dom";
import { useEffect, useRef, useState, type ReactNode } from "react";

import { getHealth } from "@/api/client";
import { Button } from "@/components/ui/button";
import { ThemeToggle } from "@/components/ui/theme-toggle";
import { Sidebar } from "./Sidebar";

function BackendStatus() {
  const [ok, setOk] = useState<boolean | null>(null);

  useEffect(() => {
    let active = true;
    getHealth()
      .then((health) => active && setOk(health.database === "connected"))
      .catch(() => active && setOk(false));
    return () => {
      active = false;
    };
  }, []);

  const label = ok === null ? "Checking…" : ok ? "Connected" : "Offline";
  const dot = ok === null ? "bg-faint" : ok ? "bg-up" : "bg-down";

  return (
    <span className="inline-flex items-center gap-2 rounded-full border border-border bg-surface px-3 py-1 text-xs text-muted-foreground">
      <span className={`h-2 w-2 rounded-full ${dot}`} aria-hidden="true" />
      {label}
    </span>
  );
}

interface AppShellProps {
  title: string;
  subtitle?: string;
  actions?: ReactNode;
  children: ReactNode;
  email: string;
  onSignOut: () => Promise<void>;
}

/** Labeled desktop navigation and a keyboard-contained mobile menu. */
export function AppShell({ title, subtitle, actions, children, email, onSignOut }: AppShellProps) {
  const location = useLocation();
  const riskRoutes = [
    ["/correlation", "Correlation"],
    ["/concentration", "Concentration"],
    ["/drawdown", "Drawdown"],
    ["/stress", "Stress test"],
  ];
  const [navOpen, setNavOpen] = useState(false);
  const drawer = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!navOpen) return;
    const previous = document.activeElement as HTMLElement | null;
    const overflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    drawer.current?.querySelector<HTMLAnchorElement>("a")?.focus();
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        event.preventDefault();
        setNavOpen(false);
      }
      if (event.key !== "Tab") return;
      const controls = drawer.current?.querySelectorAll<HTMLElement>("a, button");
      if (!controls?.length) return;
      const first = controls[0],
        last = controls[controls.length - 1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    };
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = overflow;
      previous?.focus();
    };
  }, [navOpen]);

  return (
    <div className="orbit-shell">
      <a href="#main-content" className="sr-only focus:not-sr-only">
        Skip to content
      </a>
      <div className="atlas-topbar">
        <Link to="/" className="atlas-wordmark" aria-label="Orbit home">
          ◎ orbit
        </Link>
        <nav aria-label="Primary navigation" className="atlas-topnav">
          <NavLink to="/" end>
            Overview
          </NavLink>
          <NavLink to="/holdings">Holdings</NavLink>
          <details
            className="atlas-risk-menu"
            onKeyDown={(e) => {
              if (e.key === "Escape") {
                e.currentTarget.open = false;
                e.currentTarget.querySelector("summary")?.focus();
              }
            }}
          >
            <summary>Risk &amp; exposure ▾</summary>
            <div>
              {riskRoutes.map(([to, label]) => (
                <NavLink
                  key={to}
                  to={to}
                  onClick={(e) => {
                    const menu = e.currentTarget.closest("details");
                    if (menu) menu.open = false;
                  }}
                >
                  {label}
                </NavLink>
              ))}
            </div>
          </details>
          <NavLink to="/filings">SEC filings</NavLink>
          <NavLink to="/methodology">Methodology</NavLink>
        </nav>
        <div className="atlas-account flex items-center gap-3">
          <ThemeToggle />
          <details className="atlas-risk-menu">
            <summary>Account ▾</summary>
            <div className="!left-auto right-0">
              <span title={email} className="break-all px-2 py-3 text-xs text-muted-foreground">
                {email}
              </span>
              <Button variant="ghost" onClick={() => void onSignOut()}>
                Sign out
              </Button>
            </div>
          </details>
        </div>
        <Button
          variant="outline"
          className="atlas-menu-button"
          aria-label="Open navigation"
          aria-expanded={navOpen}
          onClick={() => setNavOpen(true)}
        >
          Menu
        </Button>
      </div>
      {navOpen && (
        <div
          ref={drawer}
          role="dialog"
          aria-modal="true"
          aria-label="Navigation"
          className="fixed inset-0 z-40 lg:hidden"
        >
          <div className="absolute inset-0 overflow-y-auto bg-background p-5">
            <div className="flex justify-between">
              <ThemeToggle />
              <Button
                variant="outline"
                aria-label="Close navigation"
                onClick={() => setNavOpen(false)}
              >
                Close menu
              </Button>
            </div>
            <Sidebar email={email} onSignOut={onSignOut} onNavigate={() => setNavOpen(false)} />
          </div>
        </div>
      )}

      <main id="main-content" className="atlas-main">
        <header className="atlas-page-header">
          <div>
            <h1>{title}</h1>
            {subtitle !== undefined && <p>{subtitle}</p>}
          </div>
          <div className="flex items-center gap-3">
            {actions}
            <BackendStatus />
          </div>
        </header>
        {riskRoutes.some(([to]) => to === location.pathname) && (
          <nav aria-label="Risk views" className="atlas-risk-nav">
            {riskRoutes.map(([to, label]) => (
              <NavLink key={to} to={to}>
                {label}
              </NavLink>
            ))}
          </nav>
        )}
        {children}
        <footer className="atlas-footer">
          Historical measurements, not predictions.{" "}
          <Link to="/methodology" className="underline">
            Understand the methodology →
          </Link>
        </footer>
      </main>
    </div>
  );
}
