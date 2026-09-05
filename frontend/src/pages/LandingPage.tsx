/**
 * Public landing page: what the product does, before anyone signs in.
 *
 * Until now an unauthenticated visitor met a bare sign-in form with no explanation of what
 * they were signing into. This page answers that in plain language.
 *
 * Two deliberate choices. First, every mention of the product reads from APP_NAME, so a
 * rebrand stays a one-line change (see config/branding.ts) even though the orbital metaphor
 * is the page's whole visual identity. Second, the "what it will not do" section is not
 * modesty — EX-1 through EX-4 in the SRS are requirements, and stating them up front is
 * what separates a measurement tool from something pretending to give advice.
 */
import { Link } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { APP_NAME } from "@/config/branding";
import { OrbitDiagram } from "@/features/landing/OrbitDiagram";

const CAPABILITIES = [
  {
    title: "How much it swings",
    body: `One number for your portfolio's typical year of ups and downs, plus the same number for every holding, so you can see which ones are actually driving it.`,
  },
  {
    title: "What is secretly the same bet",
    body: `Two funds can hold different names and still move in lockstep. ${APP_NAME} finds the holdings that rise and fall together, so "diversified" becomes something you can check rather than assume.`,
  },
  {
    title: "Where too much rides on one position",
    body: `See which holdings dominate, and how many you effectively own once positions that overlap are counted as one rather than several.`,
  },
  {
    title: "The worst drop you would have sat through",
    body: `Your deepest peak-to-trough fall, how long it lasted, and whether it ever recovered.`,
  },
];

const STEPS = [
  {
    title: "Add your holdings",
    body: `Type in a ticker and a share count, or upload the CSV your brokerage already exports.`,
  },
  {
    title: "We pull the price history",
    body: `Real daily market data, stored locally so repeat analysis stays fast and stays within free data limits.`,
  },
  {
    title: "Read your risk, explained",
    body: `Every figure links to a page showing exactly how it was calculated and what it does not account for.`,
  },
];

const BOUNDARIES = [
  {
    title: "Predict prices",
    body: `No forecasts, no price targets, no signals. Nobody does this reliably, so ${APP_NAME} does not pretend to.`,
  },
  {
    title: "Tell you what to buy",
    body: `${APP_NAME} is not a financial adviser and makes no recommendations. It describes what you already own.`,
  },
  {
    title: "Ask for your brokerage login",
    body: `Your brokerage credentials are never requested, transmitted, or stored. Your accounts stay entirely under your control.`,
  },
];

function Logo() {
  return (
    <span
      className="grid h-9 w-9 place-items-center rounded-xl text-white"
      style={{ background: "linear-gradient(150deg, var(--accent), #7c5cff)" }}
      aria-hidden="true"
    >
      <svg
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2.4"
        className="h-5 w-5"
      >
        <path d="M4 19V5M4 15l4-4 3 3 5-6 4 4" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    </span>
  );
}

export function LandingPage() {
  return (
    <div className="min-h-screen">
      <header className="mx-auto flex max-w-6xl items-center justify-between px-5 py-5">
        <span className="flex items-center gap-2.5">
          <Logo />
          <span className="text-base font-semibold tracking-tight">{APP_NAME}</span>
        </span>
        <Button asChild variant="outline" size="sm">
          <Link to="/signin">Sign in</Link>
        </Button>
      </header>

      <main className="mx-auto max-w-6xl px-5">
        {/* Hero */}
        <section className="grid items-center gap-10 py-12 md:grid-cols-2 md:py-20">
          <div className="flex flex-col gap-6">
            <h1 className="text-4xl font-semibold leading-[1.1] tracking-tight md:text-5xl">
              Know what your portfolio is really doing.
            </h1>
            <p className="max-w-lg text-lg leading-relaxed text-muted-foreground">
              {APP_NAME} measures the risk already sitting in your holdings and explains it in plain
              English. Not a forecast, not advice, and never your brokerage password. Just a clear
              picture of what you own and how it moves.
            </p>
            <div className="flex flex-wrap items-center gap-3">
              <Button asChild>
                <Link to="/signin">Analyze my portfolio</Link>
              </Button>
              <span className="text-sm text-faint">Free. No brokerage connection required.</span>
            </div>
          </div>
          <div className="flex justify-center">
            <OrbitDiagram className="w-full max-w-[380px]" />
          </div>
        </section>

        {/* What it shows you */}
        <section className="border-t border-border py-14 md:py-20">
          <h2 className="text-2xl font-semibold tracking-tight md:text-3xl">
            Four questions most investors cannot answer about their own portfolio
          </h2>
          <p className="mt-3 max-w-2xl text-muted-foreground">
            You can see what you own in any brokerage account. What you usually cannot see is how
            those holdings behave together.
          </p>
          <div className="mt-9 grid gap-5 sm:grid-cols-2">
            {CAPABILITIES.map((item) => (
              <div key={item.title} className="rounded-lg border border-border bg-surface p-6">
                <h3 className="text-base font-semibold">{item.title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-muted-foreground">{item.body}</p>
              </div>
            ))}
          </div>
        </section>

        {/* How it works */}
        <section className="border-t border-border py-14 md:py-20">
          <h2 className="text-2xl font-semibold tracking-tight md:text-3xl">
            Three steps, about a minute
          </h2>
          <ol className="mt-9 grid gap-8 sm:grid-cols-3">
            {STEPS.map((step, index) => (
              <li key={step.title} className="flex flex-col gap-3">
                <span className="grid h-9 w-9 place-items-center rounded-full border border-border bg-surface-2 text-sm font-semibold text-accent">
                  {index + 1}
                </span>
                <h3 className="text-base font-semibold">{step.title}</h3>
                <p className="text-sm leading-relaxed text-muted-foreground">{step.body}</p>
              </li>
            ))}
          </ol>
        </section>

        {/* Honest boundaries */}
        <section className="border-t border-border py-14 md:py-20">
          <h2 className="text-2xl font-semibold tracking-tight md:text-3xl">
            What {APP_NAME} will not do
          </h2>
          <p className="mt-3 max-w-2xl text-muted-foreground">
            These are deliberate limits, not missing features. A tool that measures risk honestly
            has to be clear about where measurement stops.
          </p>
          <div className="mt-9 grid gap-5 sm:grid-cols-3">
            {BOUNDARIES.map((item) => (
              <div key={item.title} className="rounded-lg border border-border bg-surface p-6">
                <h3 className="flex items-center gap-2 text-base font-semibold">
                  <svg
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    className="h-4 w-4 shrink-0 text-faint"
                    aria-hidden="true"
                  >
                    <circle cx="12" cy="12" r="9" />
                    <path d="M6.5 6.5l11 11" strokeLinecap="round" />
                  </svg>
                  {item.title}
                </h3>
                <p className="mt-2 text-sm leading-relaxed text-muted-foreground">{item.body}</p>
              </div>
            ))}
          </div>
        </section>

        {/* Closing call to action */}
        <section className="border-t border-border py-14 text-center md:py-20">
          <h2 className="text-2xl font-semibold tracking-tight md:text-3xl">
            See what you actually own
          </h2>
          <p className="mx-auto mt-3 max-w-lg text-muted-foreground">
            Add a few holdings and {APP_NAME} will show you how they move, where they overlap, and
            what your worst stretch would have looked like.
          </p>
          <div className="mt-7">
            <Button asChild>
              <Link to="/signin">Get started</Link>
            </Button>
          </div>
        </section>
      </main>

      <footer className="border-t border-border">
        <div className="mx-auto flex max-w-6xl flex-col gap-1 px-5 py-8 text-xs text-faint">
          <p>
            {APP_NAME} is an educational project. It provides risk analysis, not investment advice,
            and does not execute trades.
          </p>
          <p>Market data is delayed and provided for informational purposes only.</p>
        </div>
      </footer>
    </div>
  );
}
