import { useEffect } from "react";
import { useImpact } from "../api/hooks";
import { Bars, ChartCard, SIGNAL, SimpleTable, TEAL, DEEP } from "../components/Charts";
import { QueryView } from "../components/StateViews";
import { money } from "../lib/format";

const SOURCE_NAME: Record<string, string> = { sample: "Sample data", live: "Live workspace", upload: "Your uploads" };
const KIND_NAME: Record<string, string> = {
  upload: "Upload", demo_loaded: "Sample loaded", plan_built: "Plan built", economics_saved: "Cost inputs changed",
  drop_loaded: "Drop folder", transfers_approved: "Moves approved", transfers_rejected: "Moves rejected", markdown_decided: "Markdown decided",
};

export default function Impact() {
  const impact = useImpact();
  useEffect(() => {
    document.title = "Business impact · StormSense";
  }, []);

  return (
    <>
      <h1 className="text-4xl font-extrabold">Business impact</h1>
      <p className="mt-1 max-w-3xl text-muted">
        What the plan is worth, what has changed, and the updates behind it. The money figures are estimates, and their assumptions are listed below.
      </p>
      <QueryView query={impact} rows={3}>
        {(i) => (
          <div className="mt-6 grid gap-5">
            <p className="text-sm text-muted">
              Showing: <strong className="text-ink">{SOURCE_NAME[i.source] ?? i.source}</strong>
              {i.as_of ? `, stock counted to ${i.as_of}` : ""}.
            </p>

            <dl className="grid grid-cols-2 gap-3 sm:grid-cols-5">
              {[
                ["Sales protected", money(i.headline.protected_usd)],
                ["Margin on those sales", money(i.headline.margin_usd)],
                ["Trucking", money(i.headline.trucking_usd)],
                ["Estimated profit", money(i.headline.net_usd)],
                ["Carbon (kg CO₂)", Math.round(i.headline.co2_kg).toLocaleString("en-US")],
              ].map(([label, value]) => (
                <div key={label} className="rounded-2xl bg-mist p-4">
                  <dt className="text-sm text-muted">{label}</dt>
                  <dd className="text-2xl font-extrabold">{value}</dd>
                </div>
              ))}
            </dl>

            <section aria-labelledby="changes-h" className="rounded-2xl border border-line bg-paper p-5">
              <h2 id="changes-h" className="text-xl font-extrabold">What has changed</h2>
              <p className="mt-2">
                {i.changes.last_plan_at
                  ? `The last plan was built ${i.changes.last_plan_at.replace("T", " at ")} with ${i.changes.moves_then ?? 0} moves. It now shows ${i.changes.moves_now} moves waiting for a decision.`
                  : `No plan has been built from your uploads yet. ${i.changes.moves_now} moves are waiting for a decision.`}
              </p>
            </section>

            <div className="grid gap-5 lg:grid-cols-2">
              <ChartCard title="Decisions so far" caption="Moves by where they stand now"
                table={<SimpleTable head={["Status", "Moves"]} rows={[["Waiting", i.headline.pending], ["Approved", i.headline.approved], ["Rejected", i.headline.rejected]]} />}>
                <Bars data={[{ status: "Waiting", moves: i.headline.pending }, { status: "Approved", moves: i.headline.approved }, { status: "Rejected", moves: i.headline.rejected }]}
                  x="status" y="moves" colour={[DEEP, TEAL, SIGNAL]} />
              </ChartCard>
              <section aria-labelledby="assume-h" className="rounded-2xl border border-line bg-paper p-5">
                <h2 id="assume-h" className="text-xl font-extrabold">What the figures assume</h2>
                <ul className="mt-2 list-disc space-y-2 pl-5 text-ink-soft">
                  {i.assumptions.map((a) => <li key={a}>{a}</li>)}
                </ul>
              </section>
            </div>

            <section aria-labelledby="timeline-h">
              <h2 id="timeline-h" className="text-xl font-extrabold">Updates and decisions</h2>
              {i.timeline.length === 0 ? (
                <p className="mt-2 text-muted">Nothing recorded yet. Uploads, plans, cost changes and decisions appear here as they happen.</p>
              ) : (
                <div className="mt-3 overflow-x-auto rounded-2xl border border-line">
                  <table className="w-full min-w-[36rem] text-left">
                    <thead className="bg-mist text-sm text-muted">
                      <tr>
                        <th scope="col" className="px-4 py-3">When</th>
                        <th scope="col" className="px-4 py-3">What</th>
                        <th scope="col" className="px-4 py-3">Who</th>
                        <th scope="col" className="px-4 py-3">Detail</th>
                      </tr>
                    </thead>
                    <tbody>
                      {i.timeline.map((e) => (
                        <tr key={`${e.at}-${e.kind}-${e.detail}`} className="border-t border-line">
                          <td className="px-4 py-3 text-sm text-muted">{e.at.replace("T", " ")}</td>
                          <td className="px-4 py-3 font-bold">{KIND_NAME[e.kind] ?? e.kind}</td>
                          <td className="px-4 py-3">{e.actor}</td>
                          <td className="px-4 py-3">{e.detail}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </section>
          </div>
        )}
      </QueryView>
    </>
  );
}
