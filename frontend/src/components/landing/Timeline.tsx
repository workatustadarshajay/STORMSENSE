import { motion, useScroll, useTransform, type MotionValue } from "framer-motion";
import { useRef } from "react";

const STEPS = [
  { title: "Predict", body: "Forecast each store and product for seven days, from the weather coming and the sales history." },
  { title: "Move", body: "Find the stores that will run short, and the nearby stores with spare stock. Propose the transfer." },
  { title: "Decide", body: "Each move shows its reason, the sales it protects and how sure the forecast is. Approve or reject it. Every decision is recorded." },
];

const FEED = [
  { product: "1000W generators", route: "Jacksonville to Orlando", units: 54, at: 0.55 },
  { product: "20x30 tarps", route: "Jacksonville to Tampa", units: 130, at: 0.68 },
  { product: "Submersible pumps", route: "Miami to Tampa", units: 20, at: 0.8 },
];

// One transfer row. Its status moves from Pending to Approved as the planner's step arrives.
function FeedRow({ row, progress }: { row: (typeof FEED)[number]; progress: MotionValue<number> }) {
  const approved = useTransform(progress, [row.at, row.at + 0.04], [0, 1]);
  const pendingOpacity = useTransform(approved, [0, 1], [1, 0]);
  const rowX = useTransform(progress, [row.at - 0.08, row.at], [40, 0]);
  const rowOpacity = useTransform(progress, [row.at - 0.08, row.at], [0, 1]);
  return (
    <motion.li style={{ x: rowX, opacity: rowOpacity }} className="flex items-center justify-between gap-4 rounded-2xl border border-line bg-paper px-5 py-4">
      <div>
        <p className="font-bold">{row.product}</p>
        <p className="text-sm text-muted">
          {row.route}, {row.units} units
        </p>
      </div>
      <div className="relative h-8 w-28 shrink-0">
        <motion.span style={{ opacity: pendingOpacity }} className="absolute inset-0 grid place-items-center rounded-full border border-line text-xs font-semibold text-muted">
          Pending
        </motion.span>
        <motion.span style={{ opacity: approved }} className="absolute inset-0 grid place-items-center rounded-full bg-teal text-xs font-bold text-white">
          Approved
        </motion.span>
      </div>
    </motion.li>
  );
}

// Three steps that light up one after another as you scroll, with the transfers the planner acts on.
export default function Timeline() {
  const ref = useRef<HTMLElement>(null);
  const { scrollYProgress } = useScroll({ target: ref, offset: ["start center", "end center"] });
  const lineScale = useTransform(scrollYProgress, [0, 1], [0, 1]);
  const stepOpacity = [
    useTransform(scrollYProgress, [0, 0.12, 0.3], [0.25, 1, 1]),
    useTransform(scrollYProgress, [0.3, 0.42, 0.62], [0.25, 1, 1]),
    useTransform(scrollYProgress, [0.62, 0.74, 1], [0.25, 1, 1]),
  ];

  return (
    <section ref={ref} id="how" aria-labelledby="how-h" className="relative min-h-[190vh] border-t border-line bg-paper px-6 py-24">
      <div className="sticky top-24 mx-auto grid max-w-6xl gap-16 lg:grid-cols-[1fr_1fr]">
        <div>
          <h2 id="how-h" className="max-w-md text-3xl font-extrabold tracking-tight sm:text-4xl">
            Three steps, and the planner stays in charge.
          </h2>
          <div className="relative mt-12 pl-8">
            <div aria-hidden className="absolute bottom-2 left-[9px] top-2 w-[2px] bg-line" />
            <motion.div aria-hidden style={{ scaleY: lineScale }} className="absolute bottom-2 left-[9px] top-2 w-[2px] origin-top bg-glow" />
            <ol className="grid gap-12">
              {STEPS.map((step, i) => (
                <motion.li key={step.title} style={{ opacity: stepOpacity[i] }} className="relative">
                  <span aria-hidden className="absolute -left-8 top-1.5 size-[20px] rounded-full border-2 border-teal bg-paper" />
                  <h3 className="text-2xl font-extrabold">{step.title}</h3>
                  <p className="mt-3 max-w-md leading-relaxed text-muted">{step.body}</p>
                </motion.li>
              ))}
            </ol>
          </div>
        </div>

        <div className="rounded-3xl border border-line bg-mist p-6 sm:p-8">
          <p className="text-sm font-semibold text-muted">Transfers for this week</p>
          <ul className="mt-5 grid gap-4">
            {FEED.map((row) => (
              <FeedRow key={row.product} row={row} progress={scrollYProgress} />
            ))}
          </ul>
          <p className="mt-6 text-xs text-muted">Sample data.</p>
        </div>
      </div>
    </section>
  );
}
