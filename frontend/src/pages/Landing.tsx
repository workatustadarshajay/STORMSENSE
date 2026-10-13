import { motion, MotionConfig } from "framer-motion";
import LandingHero from "../components/LandingHero";
import LandingNav from "../components/LandingNav";
import Faq from "../components/landing/Faq";
import Counters from "../components/landing/Counters";
import MagneticButton from "../components/landing/MagneticButton";
import ProductTabs from "../components/landing/ProductTabs";
import RoleSwitcher from "../components/landing/RoleSwitcher";
import ScrollProgress from "../components/landing/ScrollProgress";
import Showcase3D from "../components/landing/Showcase3D";
import TiltCard from "../components/landing/TiltCard";
import Timeline from "../components/landing/Timeline";

const CARDS = [
  { title: "Sign in once", body: "Sign in with your workspace account. Roles decide who can approve." },
  { title: "A record of every decision", body: "Every approval and rejection is recorded: who, what and when." },
  { title: "Ask, read-only", body: "Ask answers questions and cannot change data. Nothing it returns is run." },
];

const reveal = {
  initial: { opacity: 0, y: 36 },
  whileInView: { opacity: 1, y: 0 },
  viewport: { once: true, margin: "-80px" },
  transition: { duration: 0.8, ease: [0.16, 1, 0.3, 1] as const },
};

const FOOTER_COLUMNS = [
  {
    title: "Product",
    links: [
      { label: "Open the planner", href: "/today", internal: true },
      { label: "How it works", href: "#how", internal: false },
      { label: "Roles", href: "#roles", internal: false },
    ],
  },
  {
    title: "Learn",
    links: [
      { label: "Documentation", href: "https://workatustadarshajay.github.io/STORMSENSE/docs/", internal: false },
      { label: "Architecture", href: "https://workatustadarshajay.github.io/STORMSENSE/architecture/", internal: false },
      { label: "Source code", href: "https://github.com/workatustadarshajay/STORMSENSE", internal: false },
    ],
  },
];

// The first screen. The planner app starts one click away, at /today.
export default function Landing() {
  return (
    <MotionConfig reducedMotion="user">
      <div className="min-h-dvh bg-mist text-ink">
        <a href="#main" className="sr-only focus:not-sr-only focus:fixed focus:left-3 focus:top-3 focus:z-[70] focus:rounded-lg focus:bg-paper focus:px-4 focus:py-2 focus:font-bold">
          Skip to content
        </a>
        <ScrollProgress />
        <LandingNav />

        <main id="main" tabIndex={-1} className="outline-none">
          <LandingHero />

          <section className="px-6 py-24">
            <motion.div {...reveal} className="mx-auto max-w-3xl">
              <p className="text-sm font-semibold text-teal">The problem</p>
              <h2 className="mt-3 text-3xl font-extrabold tracking-tight sm:text-4xl">Storms hit the same stores at the same time.</h2>
              <p className="mt-5 text-lg leading-relaxed text-muted">
                The same products run short in the same places, all at once. In our sample history, five past storms and heat
                events lost about $302,000 of sales, mostly because stock was in the wrong store.
              </p>
            </motion.div>
          </section>

          <Showcase3D />
          <ProductTabs />
          <Timeline />
          <Counters />
          <RoleSwitcher />

          <section className="bg-paper px-6 py-24">
            <div className="mx-auto max-w-6xl">
              <motion.h2 {...reveal} className="max-w-2xl text-3xl font-extrabold tracking-tight sm:text-4xl">
                Built to be checked.
              </motion.h2>
              <div className="mt-14 grid gap-6 md:grid-cols-3">
                {CARDS.map((card, i) => (
                  <motion.div key={card.title} {...reveal} transition={{ ...reveal.transition, delay: i * 0.12 }}>
                    <TiltCard>
                      <h3 className="text-xl font-extrabold">{card.title}</h3>
                      <p className="mt-3 leading-relaxed text-muted">{card.body}</p>
                    </TiltCard>
                  </motion.div>
                ))}
              </div>
            </div>
          </section>

          <Faq />

          <section className="relative overflow-hidden bg-glow px-6 py-28 text-ink">
            <motion.div
              aria-hidden
              className="pointer-events-none absolute -left-24 -top-24 size-[420px] rounded-full bg-white/40 blur-3xl"
              animate={{ x: [0, 60, 0], y: [0, 30, 0] }}
              transition={{ duration: 14, repeat: Infinity, ease: "easeInOut" }}
            />
            <motion.div {...reveal} className="relative mx-auto flex max-w-6xl flex-col items-start gap-10 lg:flex-row lg:items-center lg:justify-between">
              <div>
                <h2 className="text-3xl font-extrabold tracking-tight sm:text-5xl">See which stores run short this week.</h2>
                <p className="mt-3 text-ink/75">Sample data is labelled throughout.</p>
              </div>
              <MagneticButton
                to="/today"
                className="inline-flex min-h-14 items-center rounded-2xl bg-ink px-7 text-lg font-extrabold text-white shadow-[0_18px_40px_rgba(16,27,43,0.3)] hover:bg-teal-deep"
              >
                Open today's plan
              </MagneticButton>
            </motion.div>
          </section>
        </main>

        <footer className="bg-ink px-6 pb-10 pt-16 text-white/80">
          <div className="mx-auto grid max-w-6xl gap-12 md:grid-cols-[1.4fr_1fr_1fr]">
            <div>
              <p className="text-xl font-extrabold text-white">
                storm<span className="text-glow">sense</span>
              </p>
              <p className="mt-3 max-w-sm leading-relaxed text-white/65">Move stock before the storm, not after. A planner approves every move.</p>
            </div>
            {FOOTER_COLUMNS.map((col) => (
              <nav key={col.title} aria-label={col.title}>
                <p className="text-sm font-bold text-white">{col.title}</p>
                <ul className="mt-4 grid gap-3">
                  {col.links.map((link) => (
                    <li key={link.label}>
                      {link.internal ? (
                        <MagneticButton to={link.href} className="hover:text-glow">
                          {link.label}
                        </MagneticButton>
                      ) : (
                        <a href={link.href} className="hover:text-glow">
                          {link.label}
                        </a>
                      )}
                    </li>
                  ))}
                </ul>
              </nav>
            ))}
          </div>
          <div className="mx-auto mt-14 flex max-w-6xl flex-wrap items-center justify-between gap-4 border-t border-white/10 pt-6 text-sm text-white/55">
            <span>Sample data is labelled throughout the app.</span>
            <a href="#main" className="hover:text-white">
              Back to top
            </a>
          </div>
        </footer>
      </div>
    </MotionConfig>
  );
}
