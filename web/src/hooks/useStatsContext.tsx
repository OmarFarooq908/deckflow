import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { fetchStats, type Stats } from "@/api";

interface StatsContextValue {
  stats: Stats | null;
  loading: boolean;
  refresh: () => Promise<void>;
}

const StatsContext = createContext<StatsContextValue | null>(null);

export function StatsProvider({ children }: { children: ReactNode }) {
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);

  async function refresh() {
    try {
      const data = await fetchStats();
      setStats(data);
    } catch {
      setStats(null);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void refresh();
  }, []);

  return (
    <StatsContext.Provider value={{ stats, loading, refresh }}>
      {children}
    </StatsContext.Provider>
  );
}

export function useStatsContext() {
  const ctx = useContext(StatsContext);
  if (!ctx) {
    throw new Error("useStatsContext must be used within StatsProvider");
  }
  return ctx;
}
