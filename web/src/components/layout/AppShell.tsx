import { NavLink, Outlet, useLocation } from "react-router-dom";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { useStatsContext } from "@/hooks/useStatsContext";

const NAV_ITEMS = [
  { to: "/", label: "Today", end: true },
  { to: "/library", label: "Library" },
  { to: "/review", label: "Review", showDue: true },
  { to: "/stats", label: "Insights" },
] as const;

export function AppNav() {
  const { stats } = useStatsContext();

  return (
    <nav className="flex gap-1 overflow-x-auto pb-1 [-ms-overflow-style:none] [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
      {NAV_ITEMS.map((item) => (
        <NavLink
          key={item.to}
          to={item.to}
          end={"end" in item ? item.end : false}
          className={({ isActive }) =>
            cn(
              "inline-flex items-center gap-2 whitespace-nowrap rounded-full px-3 py-1.5 text-sm font-medium transition-colors",
              isActive
                ? "bg-primary text-primary-foreground"
                : "bg-secondary/60 text-muted-foreground hover:bg-secondary hover:text-foreground",
            )
          }
        >
          {item.label}
          {"showDue" in item && item.showDue && stats && stats.due_today > 0 && (
            <Badge
              variant="secondary"
              className="h-5 min-w-5 justify-center bg-primary-foreground/20 px-1.5 text-[10px] text-primary-foreground"
            >
              {stats.due_today}
            </Badge>
          )}
        </NavLink>
      ))}
    </nav>
  );
}

export function AppShell() {
  const location = useLocation();
  const isLibrary = location.pathname.startsWith("/library");

  return (
    <div className="mx-auto flex min-h-screen w-full max-w-5xl flex-col px-4 py-6 sm:px-6">
      <header className="mb-8 space-y-4">
        <div className="flex flex-col gap-1 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="text-lg font-semibold tracking-tight">Deckflow</p>
            <p className="text-sm text-muted-foreground">
              Calm daily learning for git-native decks
            </p>
          </div>
        </div>
        <AppNav />
      </header>
      <main className={cn("flex-1", !isLibrary && "mx-auto w-full max-w-3xl")}>
        <Outlet />
      </main>
    </div>
  );
}
