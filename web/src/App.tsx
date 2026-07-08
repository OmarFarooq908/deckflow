import { BrowserRouter, Link, Route, Routes } from "react-router-dom";
import { HomePage } from "./pages/HomePage";
import { ReviewPage } from "./pages/ReviewPage";
import { StatsPage } from "./pages/StatsPage";

export function App() {
  return (
    <BrowserRouter>
      <div className="app-shell">
        <nav className="nav">
          <Link to="/">Home</Link>
          <Link to="/review">Review</Link>
          <Link to="/stats">Stats</Link>
        </nav>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/review" element={<ReviewPage />} />
          <Route path="/stats" element={<StatsPage />} />
        </Routes>
      </div>
    </BrowserRouter>
  );
}
