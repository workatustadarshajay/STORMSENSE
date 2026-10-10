import type { ReactNode } from "react";
import { Bar, BarChart, CartesianGrid, Cell, Line, LineChart, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

// The StormSense palette. Every chart sits beside its numbers in a table, so nothing is only in the picture.
export const TEAL = "#0097AC", DEEP = "#003C51", INK = "#231F20", SIGNAL = "#B3321F", HEAT = "#C8781A", MUTED = "#5A666E", LINE = "#DEDCD0";

export function ChartCard({ title, caption, table, children }: { title: string; caption: string; table: ReactNode; children: ReactNode }) {
  return (
    <figure className="m-0 min-w-0 rounded-2xl border border-line bg-paper p-4">
      <figcaption className="mb-2 grid gap-0.5">
        <strong className="text-base">{title}</strong>
        <span className="text-sm text-muted">{caption}</span>
      </figcaption>
      <div className="h-56 w-full">{children}</div>
      <details className="mt-2 text-sm">
        <summary className="cursor-pointer font-bold text-teal-deep">Show as a table</summary>
        <div className="mt-2 overflow-x-auto">{table}</div>
      </details>
    </figure>
  );
}

export function SimpleTable({ head, rows }: { head: string[]; rows: (string | number)[][] }) {
  return (
    <table className="w-full text-left text-sm">
      <thead className="text-muted">
        <tr>{head.map((h) => <th key={h} scope="col" className="py-1 pr-3 font-semibold">{h}</th>)}</tr>
      </thead>
      <tbody>
        {rows.map((r, i) => (
          <tr key={i} className="border-t border-line">{r.map((c, j) => <td key={j} className="py-1 pr-3">{c}</td>)}</tr>
        ))}
      </tbody>
    </table>
  );
}

export function Bars({ data, x, y, colour, unit, reference }: {
  data: Record<string, string | number>[]; x: string; y: string; colour: string | string[]; unit?: string;
  reference?: { value: number; label: string; colour: string }[];
}) {
  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart data={data} margin={{ top: 8, right: 12, bottom: 4, left: 0 }}>
        <CartesianGrid stroke={LINE} vertical={false} />
        <XAxis dataKey={x} tick={{ fill: INK, fontSize: 11 }} interval={0} />
        <YAxis tick={{ fill: MUTED, fontSize: 11 }} width={48} unit={unit} />
        <Tooltip />
        {(reference ?? []).map((r) => (
          <ReferenceLine key={r.label} y={r.value} stroke={r.colour} strokeDasharray="4 4" label={{ value: r.label, fill: r.colour, fontSize: 11 }} />
        ))}
        <Bar dataKey={y} radius={[6, 6, 0, 0]}>
          {data.map((_, i) => <Cell key={i} fill={Array.isArray(colour) ? colour[i % colour.length] : colour} />)}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

export function Trend({ data, x, y, colour, label }: { data: Record<string, string | number>[]; x: string; y: string; colour: string; label: string }) {
  return (
    <ResponsiveContainer width="100%" height="100%">
      <LineChart data={data} margin={{ top: 8, right: 12, bottom: 4, left: 0 }}>
        <CartesianGrid stroke={LINE} vertical={false} />
        <XAxis dataKey={x} tick={{ fill: MUTED, fontSize: 11 }} tickFormatter={(d: string) => d.slice(5)} />
        <YAxis tick={{ fill: MUTED, fontSize: 11 }} width={56} />
        <Tooltip formatter={(v) => [Number(v).toLocaleString("en-US"), label]} />
        <Line type="monotone" dataKey={y} stroke={colour} strokeWidth={2} dot={false} name={label} />
      </LineChart>
    </ResponsiveContainer>
  );
}
