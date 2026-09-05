/**
 * The landing page's centrepiece: holdings riding tilted orbits around a glowing core.
 *
 * The rings are ellipses rotated in the plane, which is what sells depth without any real
 * 3D: a circle seen at an angle *is* an ellipse, so three ellipses at different rotations
 * read as three orbital planes around one body.
 *
 * Tile positions are computed rather than eyeballed. A point at angle `t` on an ellipse
 * that has been rotated by `theta` is the ellipse point run through a rotation matrix, so
 * every tile sits exactly on its ring instead of approximately near it.
 *
 * Hand-authored SVG and CSS, no animation or charting library (ADR 0013).
 */

const SIZE = 560;
const CENTRE = SIZE / 2;
const RX = 248;
const RY = 92;

/** The three orbital planes, by how far each is rotated. */
const PLANES = [-20, 30, 78];

/** A point on ellipse (RX, RY) at parameter `t`, after the plane is rotated by `theta`. */
function pointOn(theta: number, t: number): { x: number; y: number } {
  const th = (theta * Math.PI) / 180;
  const a = (t * Math.PI) / 180;
  const ex = RX * Math.cos(a);
  const ey = RY * Math.sin(a);
  return {
    x: CENTRE + ex * Math.cos(th) - ey * Math.sin(th),
    y: CENTRE + ex * Math.sin(th) + ey * Math.cos(th),
  };
}

type Glyph = "wave" | "grid" | "share" | "drop" | "shield" | "clock";

/** Each tile is one thing the system measures, parked on one of the orbits. */
const TILES: { plane: number; t: number; glyph: Glyph; label: string; delay: number }[] = [
  { plane: 0, t: 178, glyph: "wave", label: "Volatility", delay: 0 },
  { plane: 0, t: 8, glyph: "grid", label: "Correlation", delay: 1.4 },
  { plane: 1, t: 200, glyph: "share", label: "Concentration", delay: 2.6 },
  { plane: 1, t: 20, glyph: "drop", label: "Drawdown", delay: 0.7 },
  { plane: 2, t: 190, glyph: "shield", label: "No credentials required", delay: 3.3 },
  { plane: 2, t: 5, glyph: "clock", label: "Cached price history", delay: 2 },
];

/** Each glyph is drawn in full rather than a shared path plus a conditionally appended
 *  circle, which made "concentration" and "cached history" both read as clocks. */
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
  share: (
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

function Tile({
  glyph,
  label,
  delay,
  x,
  y,
}: {
  glyph: Glyph;
  label: string;
  delay: number;
  x: number;
  y: number;
}) {
  return (
    <div
      className="lp-float absolute -translate-x-1/2 -translate-y-1/2"
      style={{
        left: `${(x / SIZE) * 100}%`,
        top: `${(y / SIZE) * 100}%`,
        animationDelay: `${delay}s`,
      }}
    >
      <span
        title={label}
        className="grid h-11 w-11 place-items-center rounded-[14px] border border-white/10 text-white/90 backdrop-blur-sm md:h-12 md:w-12"
        style={{
          background: "linear-gradient(150deg, rgba(124,92,255,0.85), rgba(60,40,130,0.75))",
          boxShadow: "0 8px 26px -8px rgba(124,92,255,0.9), inset 0 1px 0 rgba(255,255,255,0.18)",
        }}
      >
        <svg
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.9"
          strokeLinecap="round"
          strokeLinejoin="round"
          className="h-5 w-5"
        >
          {GLYPHS[glyph]}
        </svg>
      </span>
    </div>
  );
}

export function OrbitHero({ className }: { className?: string }) {
  return (
    <div className={`relative aspect-square ${className ?? ""}`} aria-hidden="true">
      {/* Ambient glow behind the whole system. */}
      <div
        className="lp-pulse absolute inset-0"
        style={{
          background:
            "radial-gradient(closest-side, rgba(124,92,255,0.42), rgba(124,92,255,0.10) 55%, transparent 72%)",
        }}
      />

      <svg viewBox={`0 0 ${SIZE} ${SIZE}`} className="absolute inset-0 h-full w-full">
        <defs>
          <radialGradient id="lp-core">
            <stop offset="0%" stopColor="#e9e2ff" />
            <stop offset="45%" stopColor="#9d6bff" />
            <stop offset="100%" stopColor="#4c1d95" />
          </radialGradient>
          <linearGradient id="lp-ring" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="rgba(167,139,250,0.65)" />
            <stop offset="50%" stopColor="rgba(167,139,250,0.14)" />
            <stop offset="100%" stopColor="rgba(167,139,250,0.55)" />
          </linearGradient>
        </defs>

        {PLANES.map((theta) => (
          <ellipse
            key={theta}
            cx={CENTRE}
            cy={CENTRE}
            rx={RX}
            ry={RY}
            fill="none"
            stroke="url(#lp-ring)"
            strokeWidth="1.15"
            transform={`rotate(${theta} ${CENTRE} ${CENTRE})`}
          />
        ))}

        {/* Small bodies scattered along the rings, for density. */}
        {PLANES.flatMap((theta, i) =>
          [58, 132, 246, 320].map((t) => {
            const { x, y } = pointOn(theta, t);
            return <circle key={`${i}-${t}`} cx={x} cy={y} r={2.4} fill="rgba(199,180,255,0.75)" />;
          }),
        )}

        <circle cx={CENTRE} cy={CENTRE} r={92} fill="rgba(124,92,255,0.16)" />
        <circle cx={CENTRE} cy={CENTRE} r={56} fill="url(#lp-core)" />
        <circle cx={CENTRE - 16} cy={CENTRE - 20} r={16} fill="rgba(255,255,255,0.30)" />
      </svg>

      {TILES.map((tile) => {
        const { x, y } = pointOn(PLANES[tile.plane], tile.t);
        return <Tile key={tile.label} {...tile} x={x} y={y} />;
      })}
    </div>
  );
}
