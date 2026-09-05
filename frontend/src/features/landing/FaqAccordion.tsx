import { useState } from "react";

import { APP_NAME } from "@/config/branding";

/** The questions a prospective user actually has, answered without hedging. */
const FAQ = [
  {
    q: `What does ${APP_NAME} actually do?`,
    a: `It reads the holdings you enter or import, pulls their price history, and computes four things: how much they swing, how much they move together, how concentrated you are, and how far you have fallen from a previous peak. Every figure links to a page explaining exactly how it was derived.`,
  },
  {
    q: "Do I have to connect my brokerage account?",
    a: `No, and you cannot. You type holdings in or upload the CSV your brokerage already exports. ${APP_NAME} never requests, transmits, or stores brokerage credentials, which is a deliberate design limit rather than a missing feature.`,
  },
  {
    q: "Where does the price data come from?",
    a: `Daily end-of-day prices from a market-data provider, cached locally so repeat analysis stays fast and stays inside free data limits. Prices are delayed and provided for informational purposes.`,
  },
  {
    q: `Will ${APP_NAME} tell me what to buy or sell?`,
    a: `No. ${APP_NAME} is not a financial adviser and makes no recommendations. It describes the risk in what you already own; it does not forecast prices, generate signals, or execute trades.`,
  },
  {
    q: "Why should I trust the numbers?",
    a: `Because you can check them. Every metric has a page describing the formula used, the convention chosen, why that convention was chosen over the alternatives, and what the metric does not account for. Nothing is presented as a black box.`,
  },
];

export function FaqAccordion() {
  const [open, setOpen] = useState(0);

  return (
    <div className="flex flex-col gap-3">
      {FAQ.map((item, index) => {
        const isOpen = index === open;
        return (
          <div
            key={item.q}
            className="overflow-hidden rounded-2xl border"
            style={{
              borderColor: isOpen ? "rgba(167,139,250,0.45)" : "var(--lp-line)",
              background: isOpen
                ? "linear-gradient(120deg, rgba(124,92,255,0.9), rgba(76,29,149,0.55))"
                : "var(--lp-card)",
            }}
          >
            <h3>
              <button
                type="button"
                onClick={() => setOpen(isOpen ? -1 : index)}
                aria-expanded={isOpen}
                className="flex w-full items-center justify-between gap-4 px-5 py-4 text-left text-[15px] font-medium"
              >
                <span>{item.q}</span>
                <svg
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  className={`h-4 w-4 shrink-0 transition-transform ${isOpen ? "rotate-180" : ""}`}
                  aria-hidden="true"
                >
                  <path d="M6 9l6 6 6-6" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              </button>
            </h3>
            {isOpen ? (
              <p className="px-5 pb-5 text-sm leading-relaxed text-white/85">{item.a}</p>
            ) : null}
          </div>
        );
      })}
    </div>
  );
}
