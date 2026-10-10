import { useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { SOURCE_KEY } from "../api/client";
import { useHealth, usePlanStatus } from "../api/hooks";

const CHOICES = [
  { value: "sample", label: "Sample data", hint: "Generated sample data. Works anywhere." },
  { value: "live", label: "Live workspace", hint: "The connected Databricks workspace, with live weather." },
  { value: "upload", label: "Your uploads", hint: "The plan built from the files you uploaded." },
] as const;

/** Switches every screen between the sample data and the live workspace. Live is off where the copy is not connected. */
export function DataSourceSwitch() {
  const health = useHealth();
  const plan = usePlanStatus();
  const client = useQueryClient();
  const canLive = health.data?.mode === "databricks";
  const canUpload = plan.data?.ready === true;
  const [chosen, setChosen] = useState<string | null>(() => localStorage.getItem(SOURCE_KEY));
  const current = chosen ?? (canLive ? "live" : "sample");

  // A link such as /?data=upload picks the source (the upload app links here after its demo loads).
  useEffect(() => {
    const asked = new URLSearchParams(window.location.search).get("data");
    if (asked === "sample" || asked === "live" || asked === "upload") {
      localStorage.setItem(SOURCE_KEY, asked);
      setChosen(asked);
      client.invalidateQueries();
      window.history.replaceState(null, "", window.location.pathname);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const pick = (value: string) => {
    localStorage.setItem(SOURCE_KEY, value);
    setChosen(value);
    client.invalidateQueries();
  };

  return (
    <div role="group" aria-label="Data shown" className="mb-3 grid gap-1.5">
      <span className="text-xs font-semibold text-white/70">Data shown</span>
      <div className="grid overflow-hidden rounded-xl border border-white/20 text-sm font-bold">
        {CHOICES.map((c) => {
          const off = (c.value === "live" && !canLive) || (c.value === "upload" && !canUpload);
          return (
            <button
              key={c.value}
              type="button"
              aria-pressed={current === c.value}
              disabled={off}
              title={off ? (c.value === "upload" ? "Build the plan from your uploads first." : "The live workspace is not connected on this copy.") : c.hint}
              onClick={() => pick(c.value)}
              className={`min-h-10 px-2 transition-colors ${current === c.value ? "bg-white text-ink" : "text-white/85 hover:bg-white/10"} disabled:text-white/35`}
            >
              {c.label}
            </button>
          );
        })}
      </div>
    </div>
  );
}
