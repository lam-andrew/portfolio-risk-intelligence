/**
 * The landing page's centrepiece: bodies genuinely orbiting a core.
 *
 * Depth comes from three ellipses at different rotations. A circle seen at an angle *is* an
 * ellipse, so three of them read as three orbital planes around one body, with no real 3D.
 *
 * The motion is a CSS motion path rather than a rotation. Rotating a group would only work
 * for a circle centred on the origin: these orbits are tilted ellipses, so a body has to
 * follow the actual curve. Each one gets an `offset-path` built from the same geometry that
 * draws its ring, expressed in the SVG's user units so the orbit scales with the diagram
 * instead of being pinned to pixels.
 *
 * Two details that are easy to get wrong. `offset-rotate: 0deg` keeps a body upright as it
 * travels; without it the browser turns it to face along the tangent and the icons roll
 * over. And bodies are spread around a ring with NEGATIVE animation delay, so they begin
 * part-way round rather than stacked at the start point.
 *
 * Hand-authored SVG and CSS, no animation library (ADR 0013).
 */
import type { CSSProperties } from "react";

const SIZE = 560;
const C = SIZE / 2;
const RX = 246;
const RY = 90;

/** The three orbital planes: how far each is tilted, and how long one lap takes. */
const PLANES = [
  { tilt: -20, seconds: 30 },
  { tilt: 30, seconds: 42 },
  { tilt: 78, seconds: 56 },
];

/** An ellipse as a closed path, tilted by `deg`, in SVG user units. */
function ellipsePath(deg: number): string {
  const th = (deg * Math.PI) / 180;
  const ax = C + RX * Math.cos(th);
  const ay = C + RX * Math.sin(th);
  const bx = C - RX * Math.cos(th);
  const by = C - RX * Math.sin(th);
  return `M ${ax} ${ay} A ${RX} ${RY} ${deg} 0 1 ${bx} ${by} A ${RX} ${RY} ${deg} 0 1 ${ax} ${ay}`;
}

/** Put a body on a ring at `phase` (0–1) of its lap, travelling for `seconds`. */
function orbit(plane: number, phase: number): CSSProperties {
  const { tilt, seconds } = PLANES[plane];
  return {
    offsetPath: `path("${ellipsePath(tilt)}")`,
    offsetDistance: `${phase * 100}%`,
    animationDuration: `${seconds}s`,
    animationDelay: `-${(phase * seconds).toFixed(2)}s`,
  } as CSSProperties;
}

type Glyph = "wave" | "grid" | "pie" | "drop" | "shield" | "clock";

const GLYPHS: Record<Glyph, JSX.Element> = {
  wave: <path d="M3 12c2.5-6 4.5 6 7 0s4.5-6 7 0" />,
  grid: (
    <>
      <rect x="4" y="4" width="6.5" height="6.5" rx="1.4" />
      <rect x="13.5" y="4" width="6.5" height="6.5" rx="1.4" />
      <rect x="4" y="13.5" width="6.5" height="6.5" rx="1.4" />
      <rect x="13.5" y="13.5" width="6.5" height="6.5" rx="1.4" />
    </>
  ),
  pie: (
    <>
      <circle cx="12" cy="12" r="8.5" />
      <path d="M12 3.5V12l7.4 4.2" />
    </>
  ),
  drop: <path d="M4 7l5 6 3-3 8 8" />,
  shield: <path d="M12 3l7 3v5c0 4.5-3 8-7 10-4-2-7-5.5-7-10V6z" />,
  clock: (
    <>
      <circle cx="12" cy="12" r="7.6" />
      <path d="M12 8.2V12l3 1.8" />
      <path d="M12 2.6v1.6M21.4 12h-1.6M12 21.4v-1.6M2.6 12h1.6" />
    </>
  ),
};

/** One thing the system measures, riding one of the orbits. */
const BODIES: { plane: number; phase: number; glyph: Glyph; label: string }[] = [
  { plane: 0, phase: 0.0, glyph: "wave", label: "Volatility" },
  { plane: 0, phase: 0.5, glyph: "grid", label: "Correlation" },
  { plane: 1, phase: 0.18, glyph: "pie", label: "Concentration" },
  { plane: 1, phase: 0.68, glyph: "drop", label: "Drawdown" },
  { plane: 2, phase: 0.34, glyph: "shield", label: "No credentials required" },
  { plane: 2, phase: 0.84, glyph: "clock", label: "Cached price history" },
];

/** Smaller unlabelled bodies, for the sense of a populated system. */
const MOTES = [
  { plane: 0, phase: 0.22 },
  { plane: 0, phase: 0.74 },
  { plane: 1, phase: 0.05 },
  { plane: 1, phase: 0.44 },
  { plane: 1, phase: 0.9 },
  { plane: 2, phase: 0.14 },
  { plane: 2, phase: 0.58 },
];

export function OrbitHero({ className }: { className?: string }) {
  return (
    <div className={`relative aspect-square ${className ?? ""}`} aria-hidden="true">
      <div
        className="lp-pulse absolute inset-0"
        style={{
          background:
            "radial-gradient(closest-side, rgba(74,147,240,0.34), rgba(74,147,240,0.08) 55%, transparent 72%)",
        }}
      />

      <svg viewBox={`0 0 ${SIZE} ${SIZE}`} className="absolute inset-0 h-full w-full">
        <defs>
          <radialGradient id="lp-core" cx="38%" cy="34%">
            <stop offset="0%" stopColor="#dcebff" />
            <stop offset="45%" stopColor="var(--accent)" />
            <stop offset="100%" stopColor="#12395f" />
          </radialGradient>
          <linearGradient id="lp-ring" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="var(--accent)" stopOpacity="0.55" />
            <stop offset="50%" stopColor="var(--accent)" stopOpacity="0.12" />
            <stop offset="100%" stopColor="var(--accent)" stopOpacity="0.5" />
          </linearGradient>
          <linearGradient id="lp-tile-fill" x1="0" y1="0" x2="0.35" y2="1">
            <stop offset="0%" stopColor="var(--surface-2)" />
            <stop offset="100%" stopColor="var(--surface)" />
          </linearGradient>
        </defs>

        {PLANES.map(({ tilt }) => (
          <ellipse
            key={tilt}
            cx={C}
            cy={C}
            rx={RX}
            ry={RY}
            fill="none"
            stroke="url(#lp-ring)"
            strokeWidth="1.15"
            transform={`rotate(${tilt} ${C} ${C})`}
          />
        ))}

        <circle cx={C} cy={C} r={90} fill="var(--accent)" opacity="0.13" />
        <circle cx={C} cy={C} r={54} fill="url(#lp-core)" />

        {MOTES.map((m, i) => (
          <circle
            key={i}
            className="lp-body"
            style={orbit(m.plane, m.phase)}
            r={2.6}
            fill="var(--accent)"
            opacity="0.75"
          />
        ))}

        {BODIES.map((b) => (
          <g key={b.label} className="lp-body" style={orbit(b.plane, b.phase)}>
            <title>{b.label}</title>
            <rect
              x={-23}
              y={-23}
              width={46}
              height={46}
              rx={14}
              fill="url(#lp-tile-fill)"
              stroke="var(--accent)"
              strokeOpacity="0.4"
            />
            <g
              transform="translate(-11.5 -11.5) scale(0.958)"
              fill="none"
              stroke="var(--accent)"
              strokeWidth="1.9"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              {GLYPHS[b.glyph]}
            </g>
          </g>
        ))}
      </svg>
    </div>
  );
}
