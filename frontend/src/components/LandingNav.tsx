import { motion } from "framer-motion";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

// Frosted pill navbar. The link for the section on screen is highlighted; on small screens the links sit in a menu.
const SECTIONS = [
  { id: "how", label: "How it works" },
  { id: "product", label: "Product" },
  { id: "roles", label: "Roles" },
  { id: "faq", label: "FAQ" },
];
const EXTERNAL = [
  { label: "Architecture", href: "https://workatustadarshajay.github.io/STORMSENSE/architecture/" },
  { label: "Documentation", href: "https://workatustadarshajay.github.io/STORMSENSE/docs/" },
];

function useActiveSection(ids: string[]) {
  const [active, setActive] = useState<string | null>(null);
  const key = ids.join(",");
  useEffect(() => {
    const els = key.split(",").map((id) => document.getElementById(id)).filter((el): el is HTMLElement => el !== null);
    if (typeof IntersectionObserver === "undefined" || els.length === 0) return;
    const io = new IntersectionObserver(
      (entries) => entries.forEach((e) => e.isIntersecting && setActive(e.target.id)),
      { rootMargin: "-45% 0px -50% 0px" },
    );
    els.forEach((el) => io.observe(el));
    return () => io.disconnect();
  }, [key]);
  return active;
}

export default function LandingNav() {
  const active = useActiveSection(SECTIONS.map((s) => s.id));
  const [menuOpen, setMenuOpen] = useState(false);

  return (
    <div className="fixed inset-x-0 top-4 z-50 flex justify-center px-4">
      <nav
        aria-label="Landing"
        className="relative flex animate-[settle_0.6s_ease-out_both] items-center gap-5 rounded-full border border-white/15 bg-[#0b1522]/65 py-2.5 pl-5 pr-2.5 shadow-[0_6px_24px_rgba(0,0,0,0.3)] backdrop-blur-md sm:gap-8 sm:pl-6"
      >
        <span className="text-[17px] font-extrabold tracking-tight text-white">
          storm<span className="text-glow">sense</span>
        </span>

        <ul className="hidden items-center gap-6 lg:flex">
          {SECTIONS.map(({ id, label }) => (
            <li key={id} className="relative">
              <a href={`#${id}`} aria-current={active === id ? "true" : undefined} className="whitespace-nowrap text-[13px] font-semibold text-white/70 transition-colors hover:text-white aria-[current=true]:text-white">
                {label}
              </a>
              {active === id && <motion.span layoutId="nav-dot" aria-hidden className="absolute -bottom-2 left-0 right-0 h-[2px] rounded-full bg-glow" />}
            </li>
          ))}
          {EXTERNAL.map(({ label, href }) => (
            <li key={label}>
              <a href={href} className="whitespace-nowrap text-[13px] font-semibold text-white/70 transition-colors hover:text-white">
                {label}
              </a>
            </li>
          ))}
        </ul>

        <Link to="/today" className="inline-flex min-h-9 items-center rounded-full bg-glow px-4 text-[13px] font-bold text-ink transition-colors hover:bg-white">
          Open the planner
        </Link>

        <button
          type="button"
          aria-expanded={menuOpen}
          aria-controls="landing-menu"
          onClick={() => setMenuOpen((o) => !o)}
          className="grid size-9 place-items-center rounded-full text-white hover:bg-white/10 lg:hidden"
        >
          <span className="sr-only">{menuOpen ? "Close menu" : "Open menu"}</span>
          <span aria-hidden className="grid gap-[5px]">
            <span className={`block h-[2px] w-4 bg-white transition-transform ${menuOpen ? "translate-y-[3.5px] rotate-45" : ""}`} />
            <span className={`block h-[2px] w-4 bg-white transition-transform ${menuOpen ? "-translate-y-[3.5px] -rotate-45" : ""}`} />
          </span>
        </button>

        {menuOpen && (
          <motion.ul
            id="landing-menu"
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            className="absolute left-0 right-0 top-full mt-3 grid gap-1 rounded-2xl border border-white/15 bg-[#0b1522] p-3 lg:hidden"
          >
            {[...SECTIONS.map((s) => ({ label: s.label, href: `#${s.id}` })), ...EXTERNAL].map(({ label, href }) => (
              <li key={label}>
                <a href={href} onClick={() => setMenuOpen(false)} className="block rounded-xl px-4 py-3 font-semibold text-white/85 hover:bg-white/10">
                  {label}
                </a>
              </li>
            ))}
          </motion.ul>
        )}
      </nav>
    </div>
  );
}
