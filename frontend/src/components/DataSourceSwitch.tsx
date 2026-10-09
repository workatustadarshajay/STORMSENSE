import { useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { SOURCE_KEY } from "../api/client";
import { useHealth } from "../api/hooks";

const CHOICES = [
  { value: "sample", label: "Sample data", hint: "Generated sample data. Works anywhere." },
  { value: "live", label: "Live workspace", hint: "The connected Databricks workspace, with live weather." },
] as const;

/** Switches every screen between the sample data and the live workspace. Live is off where the copy is not connected. */
export function DataSourceSwitch() {
  const health = useHealth();
  const client = useQueryClient();
  const canLive = health.data?.mode === "databricks";
  const [chosen, setChosen] = useState<string | null>(() => localStorage.getItem(SOURCE_KEY));
  const current = chosen ?? (canLive ? "live" : "sample");

  const pick = (value: string) => {
    localStorage.setItem(SOURCE_KEY, value);
    setChosen(value);
    client.invalidateQueries();
  };

  return (
    <div role="group" aria-label="Data shown" className="mb-3 grid gap-1.5">
      <span className="text-xs font-semibold text-white/70">Data shown</span>
      <div className="grid grid-cols-2 overflow-hidden rounded-xl border border-white/20 text-sm font-bold">
        {CHOICES.map((c) => {
          const off = c.value === "live" && !canLive;
          return (
            <button
              key={c.value}
              type="button"
              aria-pressed={current === c.value}
              disabled={off}
              title={off ? "The live workspace is not connected on this copy." : c.hint}
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
