// An animated storm over a map of Florida's stores. Pure SVG and CSS: no video file, no network request.
// Motion is decorative, so it stops for users who ask for reduced motion (see the rule in index.css).

const W = 1600;
const H = 900;

// Deterministic "random" values, so the scene is the same on every load.
const rnd = (i: number, salt: number) => {
  const x = Math.sin(i * 127.1 + salt * 311.7) * 43758.5453;
  return x - Math.floor(x);
};

const RAIN = Array.from({ length: 64 }, (_, i) => ({
  x: rnd(i, 1) * W,
  delay: rnd(i, 2) * 2.4,
  dur: 0.9 + rnd(i, 3) * 0.8,
  len: 26 + rnd(i, 4) * 46,
  opacity: 0.12 + rnd(i, 5) * 0.3,
}));

const STORES = [
  { name: "Jacksonville", x: 1090, y: 260 },
  { name: "Orlando", x: 1060, y: 420 },
  { name: "Tampa", x: 960, y: 455 },
  { name: "Miami", x: 1120, y: 640 },
  { name: "Tallahassee", x: 900, y: 200 },
];

// Each arc is one planned move: from a store with spare stock to a store that will run short.
const MOVES: [number, number][] = [
  [0, 1],
  [3, 2],
  [4, 2],
  [0, 2],
];

function arc(a: { x: number; y: number }, b: { x: number; y: number }) {
  const mx = (a.x + b.x) / 2;
  const my = (a.y + b.y) / 2 - 90;
  return `M ${a.x} ${a.y} Q ${mx} ${my} ${b.x} ${b.y}`;
}

export default function StormBackdrop() {
  return (
    <div aria-hidden className="pointer-events-none absolute inset-0 overflow-hidden bg-[#0b1522]">
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_50%_0%,#1d3b57_0%,transparent_60%),linear-gradient(180deg,#0b1522_0%,#101b2b_55%,#0a1420_100%)]" />

      <svg viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="xMidYMid slice" className="absolute inset-0 h-full w-full">
        <defs>
          <filter id="soft" x="-50%" y="-50%" width="200%" height="200%">
            <feGaussianBlur stdDeviation="28" />
          </filter>
          <radialGradient id="veil" cx="50%" cy="46%" r="46%">
            <stop offset="0%" stopColor="#0b1522" stopOpacity="0.85" />
            <stop offset="100%" stopColor="#0b1522" stopOpacity="0" />
          </radialGradient>
        </defs>

        {/* Clouds drifting slowly across the top. */}
        <g filter="url(#soft)">
          {[
            { cx: 200, cy: 130, rx: 360, ry: 90, dur: 38 },
            { cx: 900, cy: 90, rx: 420, ry: 110, dur: 46 },
            { cx: 1400, cy: 170, rx: 340, ry: 80, dur: 32 },
          ].map((c, i) => (
            <ellipse
              key={i}
              cx={c.cx}
              cy={c.cy}
              rx={c.rx}
              ry={c.ry}
              fill="#3d5f7d"
              opacity="0.38"
              style={{ animation: `drift ${c.dur}s ease-in-out infinite alternate` }}
            />
          ))}
        </g>

        {/* Lightning: a brief cool flash, a few times a minute. */}
        <rect width={W} height={H} fill="#bfe6ff" style={{ animation: "flash 7.5s infinite" }} />

        {/* Map: the planned moves, flowing from spare stock to shortage. */}
        {MOVES.map(([a, b], i) => (
          <path
            key={`arc-${i}`}
            d={arc(STORES[a], STORES[b])}
            fill="none"
            stroke="#73d6cd"
            strokeWidth="2"
            strokeLinecap="round"
            strokeDasharray="4 14"
            opacity="0.7"
            style={{ animation: `flow ${1.4 + i * 0.25}s linear infinite` }}
          />
        ))}

        {STORES.map((s, i) => (
          <g key={s.name}>
            <circle
              cx={s.x}
              cy={s.y}
              r="5"
              fill="none"
              stroke="#73d6cd"
              strokeWidth="1.5"
              style={{ transformBox: "fill-box", transformOrigin: "center", animation: `pulse-ring 2.6s ease-out ${i * 0.4}s infinite` }}
            />
            <circle cx={s.x} cy={s.y} r="4" fill="#73d6cd" />
          </g>
        ))}

        {/* Rain, falling past everything. */}
        {RAIN.map((r, i) => (
          <g key={`rain-${i}`} style={{ animation: `rain-fall ${r.dur}s linear ${r.delay}s infinite` }}>
            <line x1={r.x} y1={-r.len} x2={r.x - 8} y2={0} stroke="#9fd8e6" strokeWidth="1.1" opacity={r.opacity} />
          </g>
        ))}

        {/* Keeps the text area dark enough to read. */}
        <rect width={W} height={H} fill="url(#veil)" />
      </svg>
    </div>
  );
}
