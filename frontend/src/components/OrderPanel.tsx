import { useSuggestedOrders } from "../api/hooks";
import { plural } from "../lib/format";

/** What is still short after the pending moves, if demand runs high. A suggestion for the planner; nothing is ordered here. */
export function OrderPanel() {
  const orders = useSuggestedOrders();
  if (!orders.data) return null;
  const rows = orders.data;
  const total = rows.reduce((sum, r) => sum + r.order_units, 0);

  return (
    <section aria-labelledby="orders-h" className="mt-6 rounded-2xl border border-line bg-paper p-5 print:hidden">
      <h2 id="orders-h" className="text-xl font-extrabold">Still short after these moves</h2>
      {rows.length === 0 ? (
        <p className="mt-2 text-muted">The pending moves cover every store, even if demand runs high.</p>
      ) : (
        <>
          <p className="mt-1 text-sm text-muted">
            If demand runs high, these stores still run out. Suggested safety orders, for a planner to place. Nothing is ordered from here.
          </p>
          <ul className="mt-4 divide-y divide-line">
            {rows.slice(0, 6).map((r) => (
              <li key={`${r.store.id}-${r.product.id}`} className="flex flex-wrap items-center justify-between gap-3 py-3">
                <div>
                  <p className="font-bold">
                    {r.store.name}: {r.product.name_plural}
                  </p>
                  <p className="text-sm text-muted">
                    Runs out {r.stockout_day ?? "soon"}. Still short by {r.shortfall_units} if demand is as forecast.
                  </p>
                </div>
                <p className="rounded-xl bg-mist px-4 py-2 font-extrabold">Order {r.order_units}</p>
              </li>
            ))}
          </ul>
          <p className="mt-3 text-sm text-muted">
            {rows.length > 6 ? `${rows.length - 6} more. ` : ""}
            {plural(rows.length, "store and product pair")}, {total} units in all.
          </p>
        </>
      )}
    </section>
  );
}
