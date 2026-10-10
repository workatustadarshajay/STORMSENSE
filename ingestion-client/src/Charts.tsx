import {
  Bar, BarChart, Cell, CartesianGrid, Line, LineChart, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from "recharts";

// Colours from the StormSense palette. Each chart has a table beside it, so the numbers are never only in the picture.
const TEAL = "#0097ac", INK = "#231f20", SIGNAL = "#b3321f", HEAT = "#c8781a", MUTED = "#5a666e", LINE = "#dedcd0";

export function ChartCard({ title, caption, children, table }: {
  title: string; caption: string; children: React.ReactNode; table: React.ReactNode;
}) {
  return (
    <figure className="chart">
      <figcaption>
        <strong>{title}</strong>
        <span className="muted small">{caption}</span>
      </figcaption>
      <div className="chart-box">{children}</div>
      <details>
        <summary>Show as a table</summary>
        {table}
      </details>
    </figure>
  );
}

export function DailyLine({ data, dataKey, color, label }: {
  data: Record<string, string | number>[]; dataKey: string; color: string; label: string;
}) {
  return (
    <ResponsiveContainer width="100%" height={220}>
      <LineChart data={data} margin={{ top: 8, right: 12, bottom: 4, left: 0 }}>
        <CartesianGrid stroke={LINE} vertical={false} />
        <XAxis dataKey="date" tick={{ fill: MUTED, fontSize: 11 }} tickFormatter={(d: string) => d.slice(5)} />
        <YAxis tick={{ fill: MUTED, fontSize: 11 }} width={56} />
        <Tooltip formatter={(v) => [Number(v).toLocaleString("en-US"), label]} />
        <Line type="monotone" dataKey={dataKey} stroke={color} strokeWidth={2} dot={false} name={label} />
      </LineChart>
    </ResponsiveContainer>
  );
}

export function CoverBars({ data }: { data: { store: string; days: number }[] }) {
  return (
    <ResponsiveContainer width="100%" height={240}>
      <BarChart data={data} layout="vertical" margin={{ top: 8, right: 24, bottom: 4, left: 8 }}>
        <CartesianGrid stroke={LINE} horizontal={false} />
        <XAxis type="number" tick={{ fill: MUTED, fontSize: 11 }} unit=" d" />
        <YAxis type="category" dataKey="store" tick={{ fill: INK, fontSize: 12 }} width={96} />
        <Tooltip formatter={(v) => [`${v} days of stock left`, "Lowest"]} />
        <ReferenceLine x={7} stroke={SIGNAL} strokeDasharray="4 4" label={{ value: "7 days", fill: SIGNAL, fontSize: 11 }} />
        <ReferenceLine x={21} stroke={HEAT} strokeDasharray="4 4" label={{ value: "21 days", fill: HEAT, fontSize: 11 }} />
        <Bar dataKey="days" fill={TEAL} name="Days of stock left" />
      </BarChart>
    </ResponsiveContainer>
  );
}

export function StatusBars({ counts }: { counts: Record<string, number> }) {
  const data = Object.entries(counts).map(([status, count]) => ({ status, count }));
  const colour: Record<string, string> = { Short: SIGNAL, Watch: HEAT, Plenty: TEAL, "No sales": MUTED };
  return (
    <ResponsiveContainer width="100%" height={200}>
      <BarChart data={data} margin={{ top: 8, right: 12, bottom: 4, left: 0 }}>
        <CartesianGrid stroke={LINE} vertical={false} />
        <XAxis dataKey="status" tick={{ fill: INK, fontSize: 12 }} />
        <YAxis allowDecimals={false} tick={{ fill: MUTED, fontSize: 11 }} width={40} />
        <Tooltip />
        <Bar dataKey="count" name="Store and product pairs" radius={[6, 6, 0, 0]}>
          {data.map((d) => <Cell key={d.status} fill={colour[d.status] ?? TEAL} />)}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
