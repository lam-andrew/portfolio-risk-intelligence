/**
 * Public landing page: what the product does, before anyone signs in.
 *
 * The visual treatment is deliberately richer than the application's (ADR 0015). The app is
 * a tool and stays quiet so the data is the loud thing; this page is selling, so it leans on
 * the violet the brand already owns through its logo gradient.
 *
 * Two constraints shaped the content. First, every product mention reads from APP_NAME, so a
 * rebrand stays a one-line change even though the orbital metaphor is the page's whole
 * identity. Second, nothing here is invented: there are no partner logos, user counts, or
 * testimonials, because the honest versions of those do not exist yet. The numbers quoted are
 * facts about the software. The "will not do" section is not modesty either, since EX-1, EX-3
 * and EX-4 in the SRS are requirements.
 */
import { Link } from "react-router-dom";

import { APP_NAME } from "@/config/branding";
import { FaqAccordion } from "@/features/landing/FaqAccordion";
import {
  ConcentrationBars,
  CorrelationGrid,
  DrawdownCurve,
  VolatilitySpark,
} from "@/features/landing/MiniViz";
import { OrbitHero } from "@/features/landing/OrbitHero";

function Eyebrow({ children }: { children: string }) {
  return (
    <span className="lp-pill inline-block px-3.5 py-1.5 text-[11px] font-medium uppercase tracking-[0.14em] text-[color:var(--muted-foreground)]">
      {children}
    </span>
  );
}

function Arrow() {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2.2"
      className="h-3.5 w-3.5"
      aria-hidden="true"
    >
      <path d="M5 12h13M13 6l6 6-6 6" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function Logo() {
  return (
    <span className="flex items-center gap-2.5">
      <span
        className="grid h-8 w-8 place-items-center rounded-[10px] text-white"
        style={{ background: "linear-gradient(150deg, var(--accent), #1f5fb0)" }}
        aria-hidden="true"
      >
        <svg
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2.5"
          className="h-4 w-4"
        >
          <path d="M4 19V5M4 15l4-4 3 3 5-6 4 4" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </span>
      <span className="text-[15px] font-semibold tracking-tight">{APP_NAME}</span>
    </span>
  );
}

/** Facts about the software. Deliberately not user counts or transaction volumes. */
const FACTS = [
  { value: "4", label: "Dimensions of risk measured" },
  { value: "0", label: "Brokerage credentials required" },
  { value: "3", label: "Brokerage export formats read" },
];

const FEATURES = [
  {
    title: "How much it swings",
    body: "One number for your portfolio's typical year of ups and downs, plus the same number for every holding, so you can see which ones are actually driving it.",
    viz: <VolatilitySpark />,
    wide: true,
  },
  {
    title: "What is secretly the same bet",
    body: "Two funds can hold different names and still move in lockstep. Orbit finds the holdings that rise and fall together.",
    viz: <CorrelationGrid />,
    wide: false,
  },
  {
    title: "Where too much rides on one position",
    body: "See which holdings dominate, and how many you effectively own once positions that overlap are counted as one rather than several.",
    viz: <ConcentrationBars />,
    wide: false,
  },
  {
    title: "The worst drop you would have sat through",
    body: "Your deepest peak-to-trough fall, how long it lasted, and whether it ever recovered.",
    viz: <DrawdownCurve />,
    wide: true,
  },
];

const STEPS = [
  {
    title: "Add your holdings",
    body: "Type in a ticker and a share count, or upload the CSV your brokerage already exports.",
  },
  {
    title: "We pull the price history",
    body: "Real daily market data, stored locally so repeat analysis stays fast and stays within free data limits.",
  },
  {
    title: "Read your risk, explained",
    body: "Every figure links to a page showing exactly how it was calculated and what it does not account for.",
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
    body: "Your brokerage credentials are never requested, transmitted, or stored. Your accounts stay entirely under your control.",
  },
];

export function LandingPage() {
  return (
    <div className="landing min-h-screen overflow-x-hidden">
      {/* ---------------- Nav ---------------- */}
      <header className="relative z-20 mx-auto flex max-w-6xl items-center justify-between px-5 py-5">
        <Logo />
        <nav className="hidden items-center gap-7 text-sm text-[color:var(--muted-foreground)] md:flex">
          <a href="#features" className="transition-colors hover:text-white">
            Features
          </a>
          <a href="#how" className="transition-colors hover:text-white">
            How it works
          </a>
          <a href="#limits" className="transition-colors hover:text-white">
            Limits
          </a>
          <a href="#faq" className="transition-colors hover:text-white">
            FAQ
          </a>
        </nav>
        <div className="flex items-center gap-2.5">
          <Link
            to="/signin"
            className="lp-pill px-4 py-2 text-xs font-semibold uppercase tracking-wider text-[color:var(--muted-foreground)] transition-colors hover:text-white"
          >
            Log in
          </Link>
          <Link
            to="/signin"
            className="lp-cta flex items-center gap-1.5 rounded-full px-4 py-2 text-xs font-semibold uppercase tracking-wider text-white"
          >
            Get started <Arrow />
          </Link>
        </div>
      </header>

      {/* ---------------- Hero ---------------- */}
      <section className="relative overflow-hidden pb-28 pt-10 md:pb-40">
        <div className="lp-grid-fade pointer-events-none absolute inset-0" aria-hidden="true" />
        <div className="relative mx-auto grid max-w-6xl items-center gap-10 px-5 md:grid-cols-[1fr_1.05fr]">
          <div className="flex flex-col items-start gap-6">
            <Eyebrow>Portfolio risk intelligence</Eyebrow>
            <h1 className="text-[2.6rem] font-semibold leading-[1.06] tracking-tight md:text-[3.5rem]">
              Know what your portfolio is really doing.
            </h1>
            <p className="max-w-lg text-[15px] leading-relaxed text-[color:var(--muted-foreground)] md:text-base">
              {APP_NAME} measures the risk already sitting in your holdings and explains it in plain
              English. Not a forecast, not advice, and never your brokerage password. Just a clear
              picture of what you own and how it moves.
            </p>
            <div className="flex flex-wrap items-center gap-3 pt-1">
              <Link
                to="/signin"
                className="lp-cta flex items-center gap-2 rounded-full px-6 py-3 text-sm font-semibold text-white"
              >
                Analyze my portfolio <Arrow />
              </Link>
              <span className="text-sm text-[color:var(--faint)]">
                Free. No brokerage connection.
              </span>
            </div>
          </div>
          <OrbitHero className="w-full" />
        </div>

        {/* Planet-limb glow closing the section. */}
        <div
          className="pointer-events-none absolute inset-x-0 bottom-0 h-56 overflow-hidden"
          aria-hidden="true"
        >
          <div className="lp-horizon absolute inset-x-[-20%] bottom-[-58%] h-[130%] rounded-[100%]" />
          <div className="absolute inset-x-[-20%] bottom-[-58%] h-[130%] rounded-[100%] border-t border-white/15" />
        </div>
      </section>

      {/* ---------------- Honest facts ---------------- */}
      <section className="relative z-10 mx-auto max-w-6xl px-5 pb-20">
        <p className="text-center text-xs uppercase tracking-[0.16em] text-[color:var(--faint)]">
          Reads the CSV your brokerage already gives you
        </p>
        <div className="mt-5 flex flex-wrap items-center justify-center gap-x-10 gap-y-3 text-lg font-semibold text-white/45">
          <span>Schwab</span>
          <span>Fidelity</span>
          <span>Vanguard</span>
          <span className="text-sm font-normal text-[color:var(--faint)]">and most others</span>
        </div>
        <div className="mt-12 grid gap-6 sm:grid-cols-3">
          {FACTS.map((fact) => (
            <div key={fact.label} className="text-center">
              <p
                className="text-4xl font-semibold"
                style={{
                  background: "linear-gradient(180deg,#fff,var(--accent))",
                  WebkitBackgroundClip: "text",
                  backgroundClip: "text",
                  color: "transparent",
                }}
              >
                {fact.value}
              </p>
              <p className="mt-1.5 text-sm text-[color:var(--faint)]">{fact.label}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ---------------- Features ---------------- */}
      <section id="features" className="mx-auto max-w-6xl px-5 py-16 md:py-24">
        <Eyebrow>Features</Eyebrow>
        <h2 className="mt-5 max-w-2xl text-3xl font-semibold leading-tight tracking-tight md:text-[2.5rem]">
          Four questions most investors cannot answer about their own portfolio
        </h2>
        <p className="mt-4 max-w-2xl text-[color:var(--muted-foreground)]">
          You can see what you own in any brokerage account. What you usually cannot see is how
          those holdings behave together.
        </p>

        <div className="mt-10 grid gap-5 md:grid-cols-5">
          {FEATURES.map((f) => (
            <article
              key={f.title}
              className={`lp-card flex flex-col gap-4 p-6 ${f.wide ? "md:col-span-3" : "md:col-span-2"}`}
            >
              <div className="h-24 overflow-hidden rounded-xl bg-white/[0.02] p-3">{f.viz}</div>
              <div>
                <h3 className="text-lg font-semibold">{f.title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-[color:var(--muted-foreground)]">
                  {f.body}
                </p>
              </div>
            </article>
          ))}
        </div>
      </section>

      {/* ---------------- How it works ---------------- */}
      <section id="how" className="mx-auto max-w-6xl px-5 py-16 md:py-24">
        <Eyebrow>How it works</Eyebrow>
        <h2 className="mt-5 text-3xl font-semibold tracking-tight md:text-[2.5rem]">
          Three steps, about a minute
        </h2>
        <ol className="mt-10 grid gap-5 md:grid-cols-3">
          {STEPS.map((step, i) => (
            <li key={step.title} className="lp-card flex flex-col gap-3 p-6">
              <span
                className="grid h-10 w-10 place-items-center rounded-xl text-sm font-semibold text-white"
                style={{
                  background: "linear-gradient(150deg, rgba(74,147,240,0.9), rgba(18,57,95,0.7))",
                }}
              >
                {i + 1}
              </span>
              <h3 className="text-lg font-semibold">{step.title}</h3>
              <p className="text-sm leading-relaxed text-[color:var(--muted-foreground)]">
                {step.body}
              </p>
            </li>
          ))}
        </ol>
      </section>

      {/* ---------------- Limits ---------------- */}
      <section id="limits" className="mx-auto max-w-6xl px-5 py-16 md:py-24">
        <Eyebrow>Deliberate limits</Eyebrow>
        <h2 className="mt-5 text-3xl font-semibold tracking-tight md:text-[2.5rem]">
          What {APP_NAME} will not do
        </h2>
        <p className="mt-4 max-w-2xl text-[color:var(--muted-foreground)]">
          These are design decisions, not missing features. A tool that measures risk honestly has
          to be clear about where measurement stops.
        </p>
        <div className="mt-10 grid gap-5 md:grid-cols-3">
          {BOUNDARIES.map((item) => (
            <div key={item.title} className="lp-card p-6">
              <span
                className="grid h-9 w-9 place-items-center rounded-xl border border-white/10 bg-white/[0.03]"
                aria-hidden="true"
              >
                <svg
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="1.9"
                  className="h-4 w-4 text-[color:var(--faint)]"
                >
                  <circle cx="12" cy="12" r="9" />
                  <path d="M6.5 6.5l11 11" strokeLinecap="round" />
                </svg>
              </span>
              <h3 className="mt-4 text-lg font-semibold">{item.title}</h3>
              <p className="mt-2 text-sm leading-relaxed text-[color:var(--muted-foreground)]">
                {item.body}
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* ---------------- FAQ ---------------- */}
      <section id="faq" className="mx-auto max-w-3xl px-5 py-16 md:py-24">
        <div className="text-center">
          <Eyebrow>FAQ</Eyebrow>
          <h2 className="mt-5 text-3xl font-semibold tracking-tight md:text-[2.5rem]">
            Frequently asked questions
          </h2>
        </div>
        <div className="mt-10">
          <FaqAccordion />
        </div>
      </section>

      {/* ---------------- Closing ---------------- */}
      <section className="relative overflow-hidden px-5 py-24 text-center md:py-32">
        <div
          className="lp-pulse pointer-events-none absolute left-1/2 top-1/2 h-[560px] w-[860px] -translate-x-1/2 -translate-y-1/2"
          aria-hidden="true"
          style={{
            background: "radial-gradient(closest-side, rgba(74,147,240,0.32), transparent 70%)",
          }}
        />
        {/* An echo of the hero's orbits, so the page closes on the motif it opened with. */}
        <svg
          viewBox="0 0 900 320"
          aria-hidden="true"
          className="pointer-events-none absolute left-1/2 top-1/2 w-[min(900px,115vw)] -translate-x-1/2 -translate-y-1/2 opacity-70"
        >
          {[-14, 0, 14].map((tilt) => (
            <ellipse
              key={tilt}
              cx="450"
              cy="160"
              rx="380"
              ry="104"
              fill="none"
              stroke="url(#lp-close-ring)"
              strokeWidth="1"
              transform={`rotate(${tilt} 450 160)`}
            />
          ))}
          <defs>
            <linearGradient id="lp-close-ring" x1="0" y1="0" x2="1" y2="0">
              <stop offset="0%" stopColor="rgba(74,147,240,0)" />
              <stop offset="50%" stopColor="rgba(74,147,240,0.5)" />
              <stop offset="100%" stopColor="rgba(74,147,240,0)" />
            </linearGradient>
          </defs>
        </svg>
        <div className="relative mx-auto max-w-2xl">
          <h2 className="text-3xl font-semibold tracking-tight md:text-[2.75rem]">
            Put your portfolio in orbit
          </h2>
          <p className="mx-auto mt-4 max-w-lg text-[color:var(--muted-foreground)]">
            Add a few holdings and {APP_NAME} will show you how they move, where they overlap, and
            what your worst stretch would have looked like.
          </p>
          <div className="mt-8 flex justify-center">
            <Link
              to="/signin"
              className="lp-cta flex items-center gap-2 rounded-full px-7 py-3.5 text-sm font-semibold text-white"
            >
              Get started <Arrow />
            </Link>
          </div>
        </div>
      </section>

      {/* ---------------- Footer ---------------- */}
      <footer className="relative overflow-hidden border-t border-[color:var(--lp-line)]">
        <div className="mx-auto max-w-6xl px-5 pt-14">
          <div className="grid gap-10 sm:grid-cols-2">
            <div className="max-w-sm">
              <Logo />
              <p className="mt-4 text-sm leading-relaxed text-[color:var(--muted-foreground)]">
                {APP_NAME} measures, contextualizes and explains the risk already present in a
                portfolio. It is an educational project, not an investment adviser.
              </p>
            </div>
            <div className="flex flex-col gap-2 text-sm text-[color:var(--muted-foreground)] sm:items-end">
              <Link to="/signin" className="transition-colors hover:text-white">
                Sign in
              </Link>
              <a href="#features" className="transition-colors hover:text-white">
                Features
              </a>
              <a href="#limits" className="transition-colors hover:text-white">
                Deliberate limits
              </a>
              <a href="#faq" className="transition-colors hover:text-white">
                FAQ
              </a>
            </div>
          </div>

          <div className="mt-12 border-t border-[color:var(--lp-line)] py-6 text-xs text-[color:var(--faint)]">
            <p>
              {APP_NAME} provides risk analysis, not investment advice, and does not execute trades.
              Market data is delayed and provided for informational purposes only.
            </p>
          </div>
        </div>

        {/* Oversized wordmark, cropped by the viewport edge. */}
        <p
          aria-hidden="true"
          className="select-none whitespace-nowrap text-center font-semibold leading-[0.78] tracking-tighter"
          style={{
            fontSize: "clamp(5rem, 21vw, 17rem)",
            background: "linear-gradient(180deg, rgba(74,147,240,0.20), rgba(74,147,240,0))",
            WebkitBackgroundClip: "text",
            backgroundClip: "text",
            color: "transparent",
          }}
        >
          {APP_NAME}
        </p>
      </footer>
    </div>
  );
}
