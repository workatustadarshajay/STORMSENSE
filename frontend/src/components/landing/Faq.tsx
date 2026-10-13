import { AnimatePresence, motion } from "framer-motion";
import { useState } from "react";

const QUESTIONS = [
  {
    q: "Does it move stock on its own?",
    a: "No. StormSense proposes moves. A planner approves or rejects every one, and each decision is recorded.",
  },
  {
    q: "Is this running on real data?",
    a: "The screens here use sample data, and the sample label stays on. The app can read a Databricks workspace when it is set up for one. Real sales, stock and weather feeds are not connected yet.",
  },
  {
    q: "Who can see and approve?",
    a: "People sign in with their workspace account. Roles decide who can approve. Viewers can read the plan and ask questions.",
  },
  {
    q: "Is the data safe?",
    a: "The app runs with its own service principal. Every query uses fixed, parameterised statements. Uploads are off unless they are switched on.",
  },
  {
    q: "What can Ask do?",
    a: "Ask answers in one sentence with a small table. It cannot change data, and nothing it returns is run.",
  },
];

export default function Faq() {
  const [open, setOpen] = useState<number | null>(0);
  return (
    <section id="faq" aria-labelledby="faq-h" className="bg-paper px-6 py-24">
      <div className="mx-auto grid max-w-6xl gap-12 lg:grid-cols-[0.8fr_1.2fr]">
        <h2 id="faq-h" className="text-3xl font-extrabold tracking-tight sm:text-4xl">
          Questions people ask first.
        </h2>
        <ul className="divide-y divide-line border-y border-line">
          {QUESTIONS.map((item, i) => {
            const isOpen = open === i;
            return (
              <li key={item.q}>
                <h3>
                  <button
                    type="button"
                    aria-expanded={isOpen}
                    aria-controls={`faq-${i}`}
                    onClick={() => setOpen(isOpen ? null : i)}
                    className="flex min-h-14 w-full items-center justify-between gap-6 py-5 text-left text-lg font-bold"
                  >
                    {item.q}
                    <motion.span aria-hidden animate={{ rotate: isOpen ? 45 : 0 }} transition={{ duration: 0.2 }} className="text-2xl leading-none text-teal">
                      +
                    </motion.span>
                  </button>
                </h3>
                <AnimatePresence initial={false}>
                  {isOpen && (
                    <motion.div
                      id={`faq-${i}`}
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: "auto", opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
                      className="overflow-hidden"
                    >
                      <p className="pb-6 pr-10 leading-relaxed text-muted">{item.a}</p>
                    </motion.div>
                  )}
                </AnimatePresence>
              </li>
            );
          })}
        </ul>
      </div>
    </section>
  );
}
