import { animate, useInView, useReducedMotion } from "framer-motion";
import { useEffect, useRef, useState } from "react";

// A number that counts up once, when it scrolls into view.
export function CountUp({ to, format }: { to: number; format: (n: number) => string }) {
  const ref = useRef<HTMLSpanElement>(null);
  const inView = useInView(ref, { once: true, margin: "-80px" });
  const reduce = useReducedMotion();
  const [value, setValue] = useState(0);

  useEffect(() => {
    if (!inView) return;
    if (reduce) {
      setValue(to);
      return;
    }
    const controls = animate(0, to, { duration: 1.8, ease: [0.16, 1, 0.3, 1], onUpdate: setValue });
    return () => controls.stop();
  }, [inView, reduce, to]);

  return <span ref={ref}>{format(value)}</span>;
}

const STATS = [
  { to: 302154, format: (n: number) => `$${Math.round(n).toLocaleString("en-US")}`, label: "of sales lost across five past storms and heat events (sample history)" },
  { to: 4, format: (n: number) => `${Math.round(n)}%`, label: "of those lost sales protected by the current method. This is an upper bound." },
  { to: 8594, format: (n: number) => `$${Math.round(n).toLocaleString("en-US")}`, label: "net on the sample plan, after a 30% margin and trucking" },
];

export default function Counters() {
  return (
    <section aria-labelledby="numbers-h" className="bg-ink px-6 py-24 text-white">
      <div className="mx-auto max-w-6xl">
        <h2 id="numbers-h" className="max-w-2xl text-3xl font-extrabold tracking-tight sm:text-4xl">
          The gap is large, and it is measurable.
        </h2>
        <div className="mt-14 grid gap-12 md:grid-cols-3">
          {STATS.map((s) => (
            <div key={s.label} className="border-t border-white/20 pt-6">
              <p className="text-5xl font-extrabold tracking-tight text-glow sm:text-6xl">
                <CountUp to={s.to} format={s.format} />
              </p>
              <p className="mt-4 max-w-xs leading-relaxed text-white/70">{s.label}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
