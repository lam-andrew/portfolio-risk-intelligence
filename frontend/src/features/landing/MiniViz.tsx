/**
 * Miniature versions of the four things the risk engine actually computes, for the feature
 * cards. They are illustrative rather than live: the landing page is public and fetches no
 * data, so these are fixed shapes chosen to look like what the real charts look like.
 *
 * Hand-authored SVG, consistent with the application's own charts (ADR 0013).
 */

const ACCENT = "var(--accent)";

/** Volatility: a return series with visible swing. */
export function VolatilitySpark() {
  const pts = [4, 18, 9, 26, 14, 33, 21, 44, 30, 52, 38, 62];
  const d = pts.map((v, i) => `${(i / (pts.length - 1)) * 200},${70 - v}`).join(" L ");
  return (
    <svg viewBox="0 0 200 76" className="h-full w-full" aria-hidden="true">
      <defs>
        <linearGradient id="mv-vol" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={ACCENT} stopOpacity="0.42" />
          <stop offset="100%" stopColor={ACCENT} stopOpacity="0" />
        </linearGradient>
      </defs>
      <path d={`M ${d} L 200,76 L 0,76 Z`} fill="url(#mv-vol)" />
      <path d={`M ${d}`} fill="none" stroke={ACCENT} strokeWidth="2" strokeLinejoin="round" />
    </svg>
  );
}

/** Correlation: a heatmap where a few pairs are uncomfortably bright. */
export function CorrelationGrid() {
  const cells = [
    [1, 0.92, 0.31, 0.18],
    [0.92, 1, 0.27, 0.22],
    [0.31, 0.27, 1, 0.81],
    [0.18, 0.22, 0.81, 1],
  ];
  return (
    <svg viewBox="0 0 104 104" className="h-full w-full" aria-hidden="true">
      {cells.flatMap((row, i) =>
        row.map((v, j) => (
          <rect
            key={`${i}-${j}`}
            x={j * 26 + 1}
            y={i * 26 + 1}
            width={24}
            height={24}
            rx={5}
            fill={ACCENT}
            opacity={0.1 + v * 0.72}
          />
        )),
      )}
    </svg>
  );
}

/** Concentration: one position dominating the rest. */
export function ConcentrationBars() {
  const weights = [42, 19, 13, 9, 7, 5, 3, 2];
  return (
    <svg viewBox="0 0 200 76" className="h-full w-full" aria-hidden="true">
      {weights.map((w, i) => (
        <rect
          key={i}
          x={i * 25 + 3}
          y={76 - w * 1.55}
          width={18}
          height={w * 1.55}
          rx={4}
          fill={ACCENT}
          opacity={i === 0 ? 1 : 0.34}
        />
      ))}
    </svg>
  );
}

/** Drawdown: decline from a running peak, and a recovery that has not arrived. */
export function DrawdownCurve() {
  const pts = [0, -3, -9, -6, -17, -24, -21, -26, -19, -14, -16, -11];
  const d = pts
    .map((v, i) => `${(i / (pts.length - 1)) * 200},${4 + Math.abs(v) * 2.2}`)
    .join(" L ");
  return (
    <svg viewBox="0 0 200 76" className="h-full w-full" aria-hidden="true">
      <defs>
        <linearGradient id="mv-dd" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#f0655f" stopOpacity="0.40" />
          <stop offset="100%" stopColor="#f0655f" stopOpacity="0" />
        </linearGradient>
      </defs>
      <line x1="0" y1="4" x2="200" y2="4" stroke="rgba(255,255,255,0.22)" strokeWidth="1" />
      <path d={`M ${d} L 200,0 L 0,0 Z`} fill="url(#mv-dd)" />
      <path d={`M ${d}`} fill="none" stroke="#f0655f" strokeWidth="2" strokeLinejoin="round" />
    </svg>
  );
}
