import { QueryClient, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api, ApiError, type RejectReason, type WeatherMode } from "./client";

/** Waking data connections get a few patient retries; real errors get one. */
export function retryPolicy(failures: number, error: unknown): boolean {
  if (error instanceof ApiError) {
    if (error.code === "warming_up") return failures < 10;
    if (error.status >= 400 && error.status < 500) return false;
  }
  return failures < 1;
}

export const retryDelay = (attempt: number) => Math.min(1500 * 1.4 ** attempt, 8000);

export const makeQueryClient = () =>
  new QueryClient({ defaultOptions: { queries: { retry: retryPolicy, retryDelay, staleTime: 15_000, refetchOnWindowFocus: false } } });

export const useMe = () => useQuery({ queryKey: ["me"], queryFn: api.me, staleTime: 60_000 });
export const useOverview = (weather: WeatherMode = "live") =>
  useQuery({ queryKey: ["overview", weather], queryFn: () => api.overview(weather) });
export const usePending = () => useQuery({ queryKey: ["transfers", "PENDING"], queryFn: () => api.transfers("PENDING") });
export const useHistory = () => useQuery({ queryKey: ["history"], queryFn: api.history });
export const useBacktest = () => useQuery({ queryKey: ["backtest"], queryFn: api.backtest, staleTime: 300_000 });
export const useStores = (weather: WeatherMode = "live") =>
  useQuery({ queryKey: ["stores", weather], queryFn: () => api.stores(weather) });
export const useForecast = (storeId: string | undefined) =>
  useQuery({ queryKey: ["forecast", storeId], queryFn: () => api.forecast(storeId!), enabled: !!storeId });

/** Approve or reject, then refresh everything a decision changes. */
export function useDecide() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (
      v: { action: "approve"; ids: string[]; note?: string } | { action: "reject"; ids: string[]; reason: string; reasonCode: RejectReason },
    ) => (v.action === "approve" ? api.approve(v.ids, v.note) : api.reject(v.ids, v.reason, v.reasonCode)),
    onSettled: () => {
      for (const key of ["transfers", "overview", "history", "stores", "forecast"]) qc.invalidateQueries({ queryKey: [key] });
    },
  });
}

export const useAsk = () => useMutation({ mutationFn: api.ask });
export const useStormDesk = () => useMutation({ mutationFn: api.stormDesk });
export const useWhatIf = () => useMutation({ mutationFn: api.whatIf });
