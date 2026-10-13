import { motion, useScroll, useTransform } from "framer-motion";
import { useRef } from "react";
import StormBackdrop from "./StormBackdrop";
import MagneticButton from "./landing/MagneticButton";

// Full-height hero over an animated storm scene. Text is white on the dark scene and drifts away as you scroll.
const platform = ["Unity Catalog", "Serverless SQL", "Model Serving", "Lakeflow pipelines", "Genie"];

export default function LandingHero() {
  const ref = useRef<HTMLElement>(null);
  const { scrollYProgress } = useScroll({ target: ref, offset: ["start start", "end start"] });
  const contentY = useTransform(scrollYProgress, [0, 1], [0, 240]);
  const contentOpacity = useTransform(scrollYProgress, [0, 0.7], [1, 0]);
  const sceneY = useTransform(scrollYProgress, [0, 1], [0, 120]);

  return (
    <section ref={ref} className="relative flex min-h-[100svh] flex-col items-center overflow-hidden bg-[#0b1522] px-6 pt-[20vh] text-center text-white">
      <motion.div style={{ y: sceneY }} className="absolute inset-0">
        <StormBackdrop />
      </motion.div>

      <motion.div style={{ y: contentY, opacity: contentOpacity }} className="relative flex flex-col items-center">
        <motion.span
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, delay: 0.1 }}
          className="inline-flex items-center rounded-full border border-white/20 bg-white/10 px-3.5 py-1 text-xs font-semibold text-white/85 backdrop-blur-sm"
        >
          Weather-aware stock planning
        </motion.span>

        <h1 className="mt-6 max-w-[16ch] text-[clamp(2.1rem,4.8vw,3.4rem)] font-extrabold leading-[1.06] tracking-tight text-white">
          {"Move stock before the storm, not after.".split(" ").map((word, i) => (
            <motion.span
              key={`${word}-${i}`}
              initial={{ opacity: 0, y: 26, rotateX: -60 }}
              animate={{ opacity: 1, y: 0, rotateX: 0 }}
              transition={{ duration: 0.7, delay: 0.25 + i * 0.07, ease: [0.16, 1, 0.3, 1] }}
              className="mr-[0.28em] inline-block [transform-style:preserve-3d]"
            >
              {word}
            </motion.span>
          ))}
        </h1>

        <motion.p
          initial={{ opacity: 0, y: 14 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, delay: 0.7 }}
          className="mt-5 max-w-md text-[15px] font-medium leading-relaxed text-white/75"
        >
          StormSense forecasts each store's demand for the coming week, finds where stock will run short, and proposes the
          moves that protect sales. A planner approves every move.
        </motion.p>

        <motion.div initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.8, delay: 0.9 }} className="mt-8 flex flex-wrap justify-center gap-3">
          <MagneticButton
            to="/today"
            className="inline-flex min-h-12 items-center rounded-xl bg-glow px-6 font-bold text-ink shadow-[0_8px_30px_rgba(115,214,205,0.35)] transition-colors hover:bg-white"
          >
            Open today's plan
          </MagneticButton>
          <a
            href="#how"
            className="inline-flex min-h-12 items-center rounded-xl border border-white/30 bg-white/5 px-6 font-bold text-white backdrop-blur-sm transition-colors hover:bg-white/15"
          >
            How it works
          </a>
        </motion.div>
      </motion.div>

      <div className="absolute inset-x-0 bottom-0 z-10 px-6 pb-8">
        <p className="text-sm font-semibold text-white/60">Built on Databricks</p>
        <ul className="mt-3 flex flex-wrap items-center justify-center gap-x-10 gap-y-2">
          {platform.map((name) => (
            <li key={name} className="text-base font-bold text-white/80">
              {name}
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}
