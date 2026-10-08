import { useEffect, useId, useRef, type ReactNode } from "react";

/** A modal built on the native <dialog>: focus is trapped, Escape closes it, and the page behind is inert. */
export function Dialog({ open, onClose, title, children }: { open: boolean; onClose: () => void; title: string; children: ReactNode }) {
  const ref = useRef<HTMLDialogElement>(null);
  const titleId = useId();
  useEffect(() => {
    const d = ref.current;
    if (!d) return;
    if (open && !d.open) d.showModal();
    if (!open && d.open) d.close();
  }, [open]);

  return (
    <dialog
      ref={ref}
      onClose={onClose}
      aria-labelledby={titleId}
      className="m-auto w-[min(92vw,30rem)] rounded-3xl bg-paper p-0 text-ink shadow-2xl backdrop:bg-ink/55"
    >
      {open && (
        <div className="p-6">
          <h2 id={titleId} className="text-2xl font-extrabold">
            {title}
          </h2>
          {children}
        </div>
      )}
    </dialog>
  );
}
