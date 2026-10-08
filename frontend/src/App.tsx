import { QueryClientProvider } from "@tanstack/react-query";
import { Link, Route, Routes } from "react-router-dom";
import { makeQueryClient } from "./api/hooks";
import { Shell } from "./components/Shell";
import Ask from "./pages/Ask";
import History from "./pages/History";
import Stores from "./pages/Stores";
import Today from "./pages/Today";
import Transfers from "./pages/Transfers";

function NotFound() {
  return (
    <div className="mt-10 text-center">
      <h1 className="text-3xl font-extrabold">We couldn't find that page</h1>
      <Link to="/" className="mt-5 inline-flex min-h-12 items-center rounded-xl bg-ink px-5 font-bold text-white">
        Back to today
      </Link>
    </div>
  );
}

export default function App({ client = makeQueryClient() }: { client?: ReturnType<typeof makeQueryClient> }) {
  return (
    <QueryClientProvider client={client}>
      <Routes>
        <Route element={<Shell />}>
          <Route index element={<Today />} />
          <Route path="transfers" element={<Transfers />} />
          <Route path="stores" element={<Stores />} />
          <Route path="ask" element={<Ask />} />
          <Route path="history" element={<History />} />
          <Route path="*" element={<NotFound />} />
        </Route>
      </Routes>
    </QueryClientProvider>
  );
}
