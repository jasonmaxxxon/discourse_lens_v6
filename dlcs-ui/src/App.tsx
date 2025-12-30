import { BrowserRouter, Routes, Route, Navigate, useNavigate, useParams } from "react-router-dom";
import MainLayout from "./components/MainLayout";
import LogisticsDashboard from "./pages/LogisticsDashboard";
import OpsSystemVitals from "./pages/OpsSystemVitals";
import PipelineAPage from "./pages/PipelineAPage";
import PipelinePage from "./pages/PipelinePage";
import HistoryPage from "./pages/HistoryPage";
import ArchivePage from "./pages/ArchivePage";
import DemoNarrativePage from "./pages/DemoNarrativePage";
import AnalysisLoadingScreen from "./pages/AnalysisLoadingScreen";
import NarrativeDetailPage from "./pages/NarrativeDetailPage";

function NarrativeDetailRoute() {
  const { postId } = useParams();
  const navigate = useNavigate();
  if (!postId) return null;
  return <NarrativeDetailPage postId={postId} navigate={navigate} />;
}

export default function App() {
  return (
    <BrowserRouter>
      <MainLayout>
        <Routes>
          {/* Default */}
          <Route path="/" element={<Navigate to="/ops/vitals" replace />} />

          {/* New Ops (Query-driven) */}
          <Route path="/ops/vitals" element={<OpsSystemVitals />} />
          <Route path="/ops/jobs" element={<LogisticsDashboard />} />

          {/* Legacy Routes */}
          <Route path="/pipeline/a" element={<PipelineAPage />} />
          <Route path="/pipeline/b" element={<PipelinePage variant="B" />} />
          <Route path="/pipeline/c" element={<PipelinePage variant="C" />} />
          <Route path="/pipeline/progress/:jobId" element={<AnalysisLoadingScreen />} />
          <Route path="/history" element={<HistoryPage />} />
          <Route path="/archive" element={<ArchivePage />} />
          <Route path="/demo" element={<DemoNarrativePage />} />
          <Route path="/narrative/:postId" element={<NarrativeDetailRoute />} />

          {/* Fallback */}
          <Route path="*" element={<div className="p-10 text-slate-400">404 Not Found</div>} />
        </Routes>
      </MainLayout>
    </BrowserRouter>
  );
}
