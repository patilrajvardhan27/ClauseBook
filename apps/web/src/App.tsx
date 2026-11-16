import { Routes, Route } from "react-router-dom";
import { NavBar } from "./components/NavBar";
import ReviewPage from "./pages/ReviewPage";
import PlaybooksPage from "./pages/PlaybooksPage";
import SearchPage from "./pages/SearchPage";
import AnalyticsPage from "./pages/AnalyticsPage";
import AboutPage from "./pages/AboutPage";
import TermsPage from "./pages/TermsPage";
import PrivacyPage from "./pages/PrivacyPage";

// One route per page listed in the plan's section 12. Each page owns its
// own data fetching; App only lays out the shell and the nav.
export default function App() {
  return (
    <div>
      <NavBar />
      <main style={{ maxWidth: 1100, margin: "0 auto", padding: "2rem 1.5rem" }}>
        <Routes>
          <Route path="/" element={<ReviewPage />} />
          <Route path="/playbooks" element={<PlaybooksPage />} />
          <Route path="/search" element={<SearchPage />} />
          <Route path="/analytics" element={<AnalyticsPage />} />
          <Route path="/about" element={<AboutPage />} />
          <Route path="/terms" element={<TermsPage />} />
          <Route path="/privacy" element={<PrivacyPage />} />
        </Routes>
      </main>
    </div>
  );
}
