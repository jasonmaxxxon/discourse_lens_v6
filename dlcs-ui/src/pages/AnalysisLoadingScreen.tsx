import { useParams } from "react-router-dom";
import { JobExecutionMonitor } from "../components/JobExecutionMonitor";

export default function AnalysisLoadingScreen() {
  const { jobId } = useParams();

  if (!jobId) {
    return <div className="min-h-screen flex items-center justify-center bg-[#0f172a] text-white">Missing jobId</div>;
  }

  return (
    <div className="min-h-screen bg-[#0f172a] text-white flex flex-col items-center py-12 px-4">
      <div className="w-full max-w-5xl">
        <JobExecutionMonitor jobId={jobId} />
      </div>
    </div>
  );
}
