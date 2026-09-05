/**
 * The signature visual for the landing page: holdings orbiting a portfolio's centre.
 *
 * The metaphor is doing real work rather than decorating. Each ring is a volatility band,
 * so the diagram already says what the product says: the further a holding sits from the
 * centre, the more it swings. Outer rings also orbit more slowly, which is how actual
 * orbits behave and costs nothing to get right.
 *
 * Hand-authored SVG rather than a charting or animation library (ADR 0013), and the motion
 * is pure CSS so it respects `prefers-reduced-motion` (see index.css).
 */

const CENTRE = 200;

/** A holding's position on its ring, in SVG coordinates. */
function dot(radius: number, degrees: number): { cx: number; cy: number } {
  const radians = (degrees * Math.PI) / 180;
  return { cx: CENTRE + radius * Math.cos(radians), cy: CENTRE + radius * Math.sin(radians) };
}

/** radius, orbital period, dot angles, and the risk band the ring represents. */
const RINGS = [
  { radius: 78, seconds: 38, angles: [0, 140], color: "var(--up)" },
  { radius: 118, seconds: 55, angles: [40, 165, 280], color: "var(--warn)" },
  { radius: 158, seconds: 80, angles: [90, 215], color: "var(--down)" },
];

export function OrbitDiagram({ className }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 400 400"
      className={className}
      role="img"
      aria-label="Holdings orbiting a portfolio centre, grouped into rings by how much each one swings."
    >
      <defs>
        <radialGradient id="orbit-core">
          <stop offset="0%" stopColor="var(--accent)" />
          <stop offset="100%" stopColor="#7c5cff" />
        </radialGradient>
        <radialGradient id="orbit-glow">
          <stop offset="0%" stopColor="var(--accent)" stopOpacity="0.28" />
          <stop offset="70%" stopColor="var(--accent)" stopOpacity="0" />
        </radialGradient>
      </defs>

      <circle cx={CENTRE} cy={CENTRE} r={185} fill="url(#orbit-glow)" />

      {RINGS.map((ring) => (
        <g key={ring.radius}>
          <circle
            cx={CENTRE}
            cy={CENTRE}
            r={ring.radius}
            fill="none"
            stroke="var(--border)"
            strokeWidth="1"
          />
          <g
            className="orbit-ring"
            style={{ animationDuration: `${ring.seconds}s` }}
            data-testid={`orbit-ring-${ring.radius}`}
          >
            {ring.angles.map((angle) => {
              const { cx, cy } = dot(ring.radius, angle);
              return (
                <circle key={angle} cx={cx} cy={cy} r="7" fill={ring.color}>
                  <title>A holding in this volatility band</title>
                </circle>
              );
            })}
          </g>
        </g>
      ))}

      <circle cx={CENTRE} cy={CENTRE} r={34} fill="url(#orbit-core)" />
      <text
        x={CENTRE}
        y={CENTRE + 4}
        textAnchor="middle"
        className="fill-white text-[11px] font-semibold"
      >
        YOU
      </text>
    </svg>
  );
}
