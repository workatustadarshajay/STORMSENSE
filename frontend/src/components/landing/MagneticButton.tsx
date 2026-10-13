import { motion, useMotionValue, useSpring } from "framer-motion";
import { Link } from "react-router-dom";

// A button that leans toward the pointer as it approaches.
export default function MagneticButton({ to, children, className }: { to: string; children: string; className: string }) {
  const x = useSpring(useMotionValue(0), { stiffness: 260, damping: 18 });
  const y = useSpring(useMotionValue(0), { stiffness: 260, damping: 18 });
  return (
    <motion.div
      style={{ x, y, display: "inline-block" }}
      onPointerMove={(e) => {
        const r = e.currentTarget.getBoundingClientRect();
        x.set((e.clientX - (r.left + r.width / 2)) * 0.25);
        y.set((e.clientY - (r.top + r.height / 2)) * 0.25);
      }}
      onPointerLeave={() => {
        x.set(0);
        y.set(0);
      }}
    >
      <Link to={to} className={className}>
        {children}
      </Link>
    </motion.div>
  );
}
