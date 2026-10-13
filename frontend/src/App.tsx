import { lazy, Suspense } from "react";
import { QueryClientProvider } from "@tanstack/react-query";
import { Link, Route, Routes } from "react-router-dom";
import { makeQueryClient } from "./api/hooks";
import { Shell } from "./components/Shell";
import Landing from "./pages/Landing";
import Today from "./pages/Today";

// Every page except the landing page and Today loads on first visit, so the first screen downloads less.
const Ask = lazy(() => import("./pages/Ask"));
const Backtest = lazy(() => import("./pages/Backtest"));
const Analysis = lazy(() => import("./pages/Analysis"));
const Impact = lazy(() => import("./pages/Impact"));
const Loads = lazy(() => import("./pages/Loads"));
const StormResponse = lazy(() => import("./pages/StormResponse"));
const YourData = lazy(() => import("./pages/YourData"));
const History = lazy(() => import("./pages/History"));
const StormDesk = lazy(() => import("./pages/StormDesk"));
const WhatIf = lazy(() => import("./pages/WhatIf"));
const Stores = lazy(() => import("./pages/Stores"));
const Transfers = lazy(() => import("./pages/Transfers"));

function NotFound() {
  return (
    <div className="mt-10 text-center">
      <h1 className="text-3xl font-extrabold">We couldn't find that page</h1>
      <Link to="/today" className="mt-5 inline-flex min-h-12 items-center rounded-xl bg-ink px-5 font-bold text-white">
        Back to today
      </Link>
    </div>
  );
}

export default function App({ client = makeQueryClient() }: { client?: ReturnType<typeof makeQueryClient> }) {
  return (
    <QueryClientProvider client={client}>
      <Suspense fallback={<p className="mt-10 text-center text-muted">Loading…</p>}>
      <Routes>
        <Route index element={<Landing />} />
        <Route element={<Shell />}>
          <Route path="today" element={<Today />} />
          <Route path="transfers" element={<Transfers />} />
          <Route path="stores" element={<Stores />} />
          <Route path="ask" element={<Ask />} />
          <Route path="storm-desk" element={<StormDesk />} />
          <Route path="what-if" element={<WhatIf />} />
          <Route path="history" element={<History />} />
          <Route path="backtest" element={<Backtest />} />
          <Route path="your-data" element={<YourData />} />
          <Route path="analysis" element={<Analysis />} />
          <Route path="impact" element={<Impact />} />
          <Route path="response" element={<StormResponse />} />
          <Route path="loads" element={<Loads />} />
          <Route path="*" element={<NotFound />} />
        </Route>
      </Routes>
      </Suspense>
    </QueryClientProvider>
  );
}
