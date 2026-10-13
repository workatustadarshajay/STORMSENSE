import { motion, useMotionValue, useSpring, useTransform } from "framer-motion";
import type { ReactNode } from "react";

// A card that tilts toward the pointer in 3D.
export default function TiltCard({ children }: { children: ReactNode }) {
  const px = useMotionValue(0.5);
  const py = useMotionValue(0.5);
  const rotateX = useSpring(useTransform(py, [0, 1], [7, -7]), { stiffness: 220, damping: 22 });
  const rotateY = useSpring(useTransform(px, [0, 1], [-9, 9]), { stiffness: 220, damping: 22 });

  return (
    <motion.div
      onPointerMove={(e) => {
        const r = e.currentTarget.getBoundingClientRect();
        px.set((e.clientX - r.left) / r.width);
        py.set((e.clientY - r.top) / r.height);
      }}
      onPointerLeave={() => {
        px.set(0.5);
        py.set(0.5);
      }}
      style={{ rotateX, rotateY, transformPerspective: 900 }}
      className="h-full rounded-2xl border border-line bg-paper p-7 shadow-[0_18px_40px_rgba(16,27,43,0.08)] transition-shadow hover:shadow-[0_28px_60px_rgba(16,27,43,0.16)]"
    >
      {children}
    </motion.div>
  );
}
