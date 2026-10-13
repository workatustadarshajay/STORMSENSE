import { AnimatePresence, motion } from "framer-motion";
import { useState } from "react";

// Who can do what. Roles come from the workspace sign-in and the app_users table.
const ROLES = [
  {
    name: "Viewer",
    can: ["Read Today, Stores and History", "Ask questions in plain language"],
    cannot: ["Approve or reject a move"],
  },
  {
    name: "Planner",
    can: ["Everything a viewer can do", "Approve or reject transfers and storm moves"],
    cannot: [],
  },
  {
    name: "Admin",
    can: ["Approve or reject, as a planner does", "Roles are kept in the app_users table"],
    cannot: [],
  },
  {
    name: "Data owner",
    can: ["Upload the four feeds: stores, products, sales and stock", "Replace one feed at a time"],
    cannot: ["Approve or reject a move"],
  },
  {
    name: "AI assistant",
    can: ["Use MCP tools, under the same rules as the app"],
    cannot: ["Skip the app's roles and approval rules"],
  },
];

export default function RoleSwitcher() {
  const [index, setIndex] = useState(1);
  const role = ROLES[index];
  return (
    <section id="roles" aria-labelledby="roles-h" className="bg-mist px-6 py-24">
      <div className="mx-auto max-w-6xl">
        <h2 id="roles-h" className="text-3xl font-extrabold tracking-tight sm:text-4xl">
          Who can do what.
        </h2>
        <div role="radiogroup" aria-label="Role" className="mt-10 flex flex-wrap gap-2">
          {ROLES.map((r, i) => (
            <button
              key={r.name}
              type="button"
              role="radio"
              aria-checked={i === index}
              onClick={() => setIndex(i)}
              className={`min-h-11 rounded-full border px-5 font-bold transition-colors ${
                i === index ? "border-ink bg-ink text-white" : "border-line bg-paper text-ink hover:border-teal"
              }`}
            >
              {r.name}
            </button>
          ))}
        </div>

        <div className="mt-8 grid gap-6 rounded-3xl border border-line bg-paper p-6 sm:p-8 md:grid-cols-2">
          <AnimatePresence mode="wait">
            <motion.div key={role.name} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }} transition={{ duration: 0.25 }} className="contents">
              <div>
                <p className="text-sm font-semibold text-muted">Can</p>
                <ul className="mt-3 grid gap-3">
                  {role.can.map((c) => (
                    <li key={c} className="flex gap-3 leading-relaxed">
                      <span aria-hidden className="mt-1.5 size-2 shrink-0 rounded-full bg-teal" />
                      {c}
                    </li>
                  ))}
                </ul>
              </div>
              <div>
                <p className="text-sm font-semibold text-muted">Cannot</p>
                <ul className="mt-3 grid gap-3">
                  {role.cannot.length === 0 && <li className="text-muted">Nothing outside the app's rules.</li>}
                  {role.cannot.map((c) => (
                    <li key={c} className="flex gap-3 leading-relaxed text-muted">
                      <span aria-hidden className="mt-1.5 size-2 shrink-0 rounded-full bg-line" />
                      {c}
                    </li>
                  ))}
                </ul>
              </div>
            </motion.div>
          </AnimatePresence>
        </div>
      </div>
    </section>
  );
}
