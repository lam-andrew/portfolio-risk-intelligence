import { APP_NAME } from "@/config/branding";
import { Link } from "react-router-dom";
import { ThemeToggle } from "@/components/ui/theme-toggle";
import { LineChart } from "@/components/charts/LineChart";
import { AllocationChart } from "@/components/charts/AllocationChart";
import { FaqAccordion } from "@/features/landing/FaqAccordion";
import type { Position } from "@/api/client";

// Public, clearly labeled product illustration. Never used in authenticated analysis.
const illustrative = [
  108, 111, 110, 116, 120, 118, 123, 119, 115, 108, 103, 105, 108, 114, 118, 115, 121, 126, 123,
  128,
];
const positions: Position[] = [32, 26, 22, 12, 8].map((weight, id) => ({
  id,
  ticker: ["MSFT", "AAPL", "VTI", "BND", "VXUS"][id],
  quantity: "1",
  latest_price: null,
  market_value: null,
  price_as_of: null,
  weight_pct: String(weight),
}));
export function LandingPage() {
  return (
    <div className="landing min-h-screen">
      <header className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-6 py-7">
        <Link to="/" className="atlas-wordmark">
          ◎ orbit
        </Link>
        <nav
          aria-label="Public navigation"
          className="hidden gap-8 text-sm text-muted-foreground md:flex"
        >
          <a href="#features">Features</a>
          <a href="#how">How it works</a>
          <a href="#faq">FAQ</a>
        </nav>
        <div className="flex flex-wrap items-center justify-end gap-3">
          <ThemeToggle />
          <Link className="rounded-xl bg-accent px-4 py-3 text-sm text-white" to="/signin">
            Log in
          </Link>
        </div>
      </header>
      <main className="mx-auto max-w-7xl px-6 pb-16">
        <section className="py-12 text-center sm:py-20">
          <p className="mb-6 font-mono text-xs uppercase tracking-widest text-muted-foreground">
            Portfolio risk intelligence
          </p>
          <h1 className="text-4xl font-medium leading-tight sm:text-6xl">
            Know what you own.
            <br />
            Understand what could hurt it.
          </h1>
          <p className="mx-auto mt-6 max-w-xl text-muted-foreground">
            See the risk already in your holdings through clear measurements and evidence you can
            inspect.
          </p>
          <Link
            to="/signin"
            className="mt-8 inline-block rounded-xl bg-accent px-6 py-3 text-sm text-white"
          >
            Analyze my portfolio →
          </Link>
          <p className="mt-4 text-xs text-muted-foreground">No brokerage credentials required.</p>
        </section>
        <section aria-label="Illustrative product preview">
          <p className="mb-4 font-mono text-xs text-muted-foreground">
            ILLUSTRATIVE EXAMPLE · NOT A REAL PORTFOLIO
          </p>
          <div className="atlas-hero-grid">
            <div className="orbit-panel border border-border p-6">
              <h2 className="mb-3 text-xl">Your portfolio in perspective</h2>
              <p className="mb-6 text-xs text-muted-foreground">
                Sample historical replay, not actual investment return.
              </p>
              <LineChart
                points={illustrative.map((value, i) => ({
                  date: `2026-09-${String(i + 1).padStart(2, "0")}`,
                  value: value * 1000,
                }))}
                label="Illustrative portfolio value"
                unit="Sample value · USD"
                formatValue={(v) => `$${v.toLocaleString()}`}
              />
            </div>
            <div className="orbit-panel border border-border p-6">
              <h2 className="mb-5 text-xl">The shape of your exposure</h2>
              <AllocationChart positions={positions} />
            </div>
          </div>
        </section>
        <section id="features" className="py-16">
          <h2 className="mb-8 text-3xl">A portfolio is more than a list of tickers.</h2>
          <div className="grid gap-6 md:grid-cols-3">
            {[
              [
                "01",
                "Measure the movement",
                "Volatility and historical drawdown describe how your holdings have moved.",
              ],
              [
                "02",
                "See the concentration",
                "Inspect position weights and price co-movement. Fund constituent look-through is not included.",
              ],
              [
                "03",
                "Explore a scenario",
                "Apply explicit price-shock assumptions. See the impact on every holding.",
              ],
            ].map(([n, title, body]) => (
              <article key={n} className="rounded-2xl border border-border bg-surface p-7">
                <span className="font-mono text-sm text-muted-foreground">{n}</span>
                <h3 className="my-4 text-xl">{title}</h3>
                <p className="text-sm leading-relaxed text-muted-foreground">{body}</p>
              </article>
            ))}
          </div>
        </section>
        <div className="atlas-evidence">
          <div>
            <h2 className="text-2xl">Go beyond the number. Read the evidence.</h2>
            <p className="mt-3 text-sm text-muted-foreground">
              Explore indexed SEC disclosures and trace grounded answers to source passages.
            </p>
          </div>
          <Link to="/signin" className="text-sm underline">
            Explore Orbit →
          </Link>
        </div>
        <section id="how" className="py-16">
          <h2 className="mb-6 text-3xl">From holdings to understanding.</h2>
          {[
            "Add your holdings manually or import a brokerage CSV.",
            "Let cached market prices provide historical context.",
            "Explore the measurements, methodology and source evidence.",
          ].map((s, i) => (
            <p key={s} className="border-b border-border py-6">
              <span className="mr-5 font-mono text-muted-foreground">0{i + 1}</span>
              {s}
            </p>
          ))}
        </section>
        <section className="mb-16">
          <h2 className="mb-6 text-3xl">What {APP_NAME} will not do</h2>
          <div className="grid gap-6 md:grid-cols-3">
            {[
              [
                "Predict prices",
                "Historical measurements describe observed behavior; they do not forecast returns.",
              ],
              [
                "Tell you what to buy",
                "Orbit provides no trade execution, recommendations or personalized investment advice.",
              ],
              [
                "Ask for your brokerage login",
                "Enter quantities or import a CSV. Your brokerage credentials stay with you.",
              ],
            ].map(([title, body]) => (
              <article key={title}>
                <h3 className="mb-3 text-xl">{title}</h3>
                <p className="text-sm text-muted-foreground">{body}</p>
              </article>
            ))}
          </div>
        </section>
        <section id="faq" className="mx-auto max-w-3xl">
          <h2 className="mb-8 text-3xl">Clarity includes knowing the limits.</h2>
          <FaqAccordion />
        </section>
        <section className="mt-16 rounded-2xl bg-surface-2 p-8">
          <h2 className="mb-5 text-3xl">Put your portfolio in perspective.</h2>
          <Link
            to="/signin"
            className="inline-block rounded-xl bg-accent px-5 py-3 text-sm text-white"
          >
            Get started →
          </Link>
        </section>
        <footer className="atlas-footer">
          Historical measurements. No forecasts, trades or investment advice.
        </footer>
      </main>
    </div>
  );
}
