import { Routes, Route, Navigate } from "react-router-dom";
import Layout from "./components/Layout";
import SessionsPage from "./pages/SessionsPage";
import StrategiesPage from "./pages/StrategiesPage";
import StrategyDetailPage from "./pages/StrategyDetailPage";
import NewStrategyPage from "./pages/NewStrategyPage";
import NewSessionPage from "./pages/NewSessionPage";
import NewLivePage from "./pages/NewLivePage";
import SessionDetailPage from "./pages/SessionDetailPage";

export default function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Navigate to="/sessions" replace />} />
        <Route path="/sessions" element={<SessionsPage />} />
        <Route path="/sessions/new" element={<NewSessionPage />} />
        <Route path="/sessions/new/live" element={<NewLivePage />} />
        <Route path="/sessions/:id" element={<SessionDetailPage />} />
        <Route path="/strategies" element={<StrategiesPage />} />
        <Route path="/strategies/new" element={<NewStrategyPage />} />
        <Route path="/strategies/:id" element={<StrategyDetailPage />} />
      </Routes>
    </Layout>
  );
}