import type { UseQueryResult } from "@tanstack/react-query";
import { CloudOff, LoaderCircle } from "lucide-react";
import type { ReactNode } from "react";
import { ApiError } from "../api/client";

export function Loading({ rows = 3 }: { rows?: number }) {
  return (
    <div role="status" aria-busy="true" className="grid gap-3">
      <span className="sr-only">Loading</span>
      {Array.from({ length: rows }, (_, i) => (
        <div key={i} className="skeleton h-24" />
      ))}
    </div>
  );
}

export function Warming() {
  return (
    <div role="status" className="flex items-start gap-3 rounded-2xl bg-teal-tint p-5 text-teal-deep">
      <LoaderCircle className="mt-0.5 size-6 shrink-0 animate-spin" aria-hidden />
      <div>
        <p className="font-bold">Getting things ready</p>
        <p className="text-sm">This usually takes a few seconds. We'll keep trying.</p>
      </div>
    </div>
  );
}

export function Empty({ title, children, action }: { title: string; children?: ReactNode; action?: ReactNode }) {
  return (
    <div className="rounded-2xl border border-dashed border-line bg-paper p-8 text-center">
      <p className="text-lg font-bold">{title}</p>
      {children && <p className="mx-auto mt-1 text-muted">{children}</p>}
      {action && <div className="mt-5 flex justify-center">{action}</div>}
    </div>
  );
}

export function ErrorState({ error, retry }: { error: unknown; retry?: () => void }) {
  const e = error instanceof ApiError ? error : null;
  const signedOut = e?.code === "signed_out";
  return (
    <div role="alert" className="flex items-start gap-3 rounded-2xl bg-signal-tint p-5 text-signal-deep">
      <CloudOff className="mt-0.5 size-6 shrink-0" aria-hidden />
      <div>
        <p className="font-bold">{signedOut ? "Please sign in again" : "That didn't load"}</p>
        <p className="text-sm">{e?.message ?? "Something went wrong. Please try again."}</p>
        <button
          type="button"
          onClick={signedOut ? () => window.location.reload() : retry}
          className="mt-3 min-h-11 rounded-xl bg-signal-deep px-4 font-bold text-white hover:bg-signal"
        >
          {signedOut ? "Reload" : "Try again"}
        </button>
      </div>
    </div>
  );
}

/** One place for loading, waking-up, error and empty states, so no screen is a dead end. */
export function QueryView<T>({
  query,
  children,
  isEmpty,
  empty,
  rows,
}: {
  query: UseQueryResult<T>;
  children: (data: T) => ReactNode;
  isEmpty?: (data: T) => boolean;
  empty?: ReactNode;
  rows?: number;
}) {
  if (query.isPending) {
    const waking = query.failureReason instanceof ApiError && query.failureReason.code === "warming_up";
    return waking ? <Warming /> : <Loading rows={rows} />;
  }
  if (query.isError) return <ErrorState error={query.error} retry={() => query.refetch()} />;
  if (isEmpty?.(query.data)) return <>{empty}</>;
  return <>{children(query.data)}</>;
}
