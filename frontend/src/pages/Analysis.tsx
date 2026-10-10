import { useEffect } from "react";
import { useAnalysisCharts } from "../api/hooks";
import { Bars, ChartCard, DEEP, HEAT, SimpleTable, SIGNAL, TEAL, Trend } from "../components/Charts";
import { QueryView } from "../components/StateViews";
import { money } from "../lib/format";

export default function Analysis() {
  const charts = useAnalysisCharts();
  useEffect(() => {
    document.title = "Analysis · StormSense";
  }, []);

  return (
    <>
      <h1 className="text-4xl font-extrabold">Analysis</h1>
      <p className="mt-1 max-w-3xl text-muted">
        The plan in pictures: the demand coming up, the shortages, the moves waiting, and where the protected sales are. Each chart has its numbers in a table.
      </p>
      <QueryView query={charts} rows={3}>
        {(c) => (
          <div className="mt-6 grid gap-5 lg:grid-cols-2">
            <ChartCard title="Demand this week" caption={`Units expected to sell each day, against ${c.stock_available.toLocaleString("en-US")} units available`}
              table={<SimpleTable head={["Date", "Units expected"]} rows={c.demand_by_day.map((d) => [d.date, d.units])} />}>
              <Trend data={c.demand_by_day} x="date" y="units" colour={DEEP} label="Units expected" />
            </ChartCard>
            <ChartCard title="Shortages by store" caption="Products each store is projected to run short of this week"
              table={<SimpleTable head={["Store", "Products short"]} rows={c.shortages_by_store.map((s) => [s.store, s.count])} />}>
              <Bars data={c.shortages_by_store} x="store" y="count" colour={SIGNAL} />
            </ChartCard>
            <ChartCard title="Moves by urgency" caption="Pending moves, and the sales each group protects"
              table={<SimpleTable head={["Urgency", "Moves", "Sales protected"]} rows={c.transfers_by_urgency.map((u) => [u.urgency, u.moves, money(u.protected_usd)])} />}>
              <Bars data={c.transfers_by_urgency} x="urgency" y="protected_usd" colour={[SIGNAL, TEAL]} unit="" />
            </ChartCard>
            <ChartCard title="Protected sales by product" caption="Gross sales the pending moves protect (not profit)"
              table={<SimpleTable head={["Product", "Sales protected"]} rows={c.protected_by_product.map((p) => [p.product, money(p.protected_usd)])} />}>
              <Bars data={c.protected_by_product} x="product" y="protected_usd" colour={HEAT} />
            </ChartCard>
          </div>
        )}
      </QueryView>
    </>
  );
}
