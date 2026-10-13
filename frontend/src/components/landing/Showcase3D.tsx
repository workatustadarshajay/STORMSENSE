import { motion, useScroll, useTransform } from "framer-motion";
import { useRef } from "react";

const LAYERS = [
  { label: "Forecast", detail: "Seven days per store and product, from the weather and the sales history." },
  { label: "Gaps", detail: "Where stock will run short, and the first day it happens." },
  { label: "Moves", detail: "The nearest spare stock, waiting for a planner's decision." },
];

// A browser window that rises out of the page in 3D as you scroll, and separates into its data layers.
export default function Showcase3D() {
  const ref = useRef<HTMLElement>(null);
  const { scrollYProgress } = useScroll({ target: ref, offset: ["start end", "end start"] });

  const rotateX = useTransform(scrollYProgress, [0, 0.45], [42, 0]);
  const rotateY = useTransform(scrollYProgress, [0, 0.45], [-14, 0]);
  const scale = useTransform(scrollYProgress, [0, 0.45], [0.8, 1]);
  const opacity = useTransform(scrollYProgress, [0, 0.2], [0.25, 1]);
  const spread = useTransform(scrollYProgress, [0.3, 0.8], [0, 1]);
  const z1 = useTransform(spread, [0, 1], [0, 60]);
  const z2 = useTransform(spread, [0, 1], [0, 130]);
  const z3 = useTransform(spread, [0, 1], [0, 200]);
  const layerOpacity = useTransform(spread, [0, 0.6], [0, 1]);
  const itemOpacity = [
    useTransform(spread, [0, 0.5], [0.3, 1]),
    useTransform(spread, [0.15, 0.65], [0.3, 1]),
    useTransform(spread, [0.3, 0.8], [0.3, 1]),
  ];

  return (
    <section ref={ref} aria-labelledby="showcase-h" className="relative h-[230vh] bg-mist">
      <div className="sticky top-0 flex h-screen items-center overflow-hidden px-6">
        <div className="mx-auto grid w-full max-w-6xl items-center gap-14 lg:grid-cols-[0.8fr_1.2fr]">
          <div>
            <h2 id="showcase-h" className="text-3xl font-extrabold tracking-tight sm:text-4xl">
              Everything a planner needs on one screen.
            </h2>
            <ul className="mt-10 grid gap-6">
              {LAYERS.map((layer, i) => (
                <motion.li
                  key={layer.label}
                  style={{ opacity: itemOpacity[i] }}
                  className="border-l-2 border-teal pl-5"
                >
                  <p className="text-lg font-extrabold">{layer.label}</p>
                  <p className="mt-1 leading-relaxed text-muted">{layer.detail}</p>
                </motion.li>
              ))}
            </ul>
          </div>

          <div className="relative" style={{ perspective: "1400px" }}>
            <motion.div style={{ rotateX, rotateY, scale, opacity, transformStyle: "preserve-3d" }} className="relative">
              <motion.div aria-hidden style={{ translateZ: z1, opacity: layerOpacity }} className="absolute inset-x-6 -bottom-4 h-full rounded-2xl border border-teal/40 bg-teal/10" />
              <motion.div aria-hidden style={{ translateZ: z2, opacity: layerOpacity }} className="absolute inset-x-12 -bottom-8 h-full rounded-2xl border border-[#1d5b8a]/40 bg-[#1d5b8a]/10" />
              <motion.div aria-hidden style={{ translateZ: z3, opacity: layerOpacity }} className="absolute inset-x-20 -bottom-12 h-full rounded-2xl border border-[#7a4a00]/35 bg-[#7a4a00]/10" />

              <div className="relative overflow-hidden rounded-2xl border border-line bg-paper shadow-[0_30px_80px_rgba(16,27,43,0.22)]">
                <div className="flex items-center gap-2 border-b border-line bg-mist px-4 py-3" aria-hidden>
                  <span className="size-2.5 rounded-full bg-[#e7a3a0]" />
                  <span className="size-2.5 rounded-full bg-[#f1d28a]" />
                  <span className="size-2.5 rounded-full bg-[#9fd9cf]" />
                  <span className="ml-3 rounded-md bg-paper px-3 py-0.5 text-xs font-semibold text-muted">stormsense / today</span>
                </div>
                <img
                  src="/landing/today.png"
                  alt="The Today screen of StormSense, with urgent transfers, stores running low and the next weather alert"
                  width={1440}
                  height={1000}
                  loading="lazy"
                  className="block h-auto w-full"
                />
              </div>
            </motion.div>
            <p className="mt-6 text-sm text-muted">Sample data. Screen from the planner app.</p>
          </div>
        </div>
      </div>
    </section>
  );
}
