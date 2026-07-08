import { BrowserRouter, Route, Routes } from "react-router-dom";
import { TooltipProvider } from "@/components/ui/tooltip";
import { AppShell } from "@/components/layout/AppShell";
import { StatsProvider } from "@/hooks/useStatsContext";
import { HomePage } from "@/pages/HomePage";
import { LibraryPage } from "@/pages/LibraryPage";
import { ReviewPage } from "@/pages/ReviewPage";
import { StatsPage } from "@/pages/StatsPage";

export function App() {
  return (
    <BrowserRouter>
      <StatsProvider>
        <TooltipProvider>
          <Routes>
            <Route element={<AppShell />}>
              <Route path="/" element={<HomePage />} />
              <Route path="/library" element={<LibraryPage />} />
              <Route path="/review" element={<ReviewPage />} />
              <Route path="/stats" element={<StatsPage />} />
            </Route>
          </Routes>
        </TooltipProvider>
      </StatsProvider>
    </BrowserRouter>
  );
}
