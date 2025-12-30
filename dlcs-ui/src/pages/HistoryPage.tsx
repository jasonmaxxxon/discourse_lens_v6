export default function HistoryPage() {
  return (
    <div className="p-8 space-y-4">
      <h2 className="text-2xl font-bold">History</h2>
      <p className="text-white/70">近期分析紀錄列表（待串接 API /api/posts）。</p>
      <div className="glass-panel rounded-xl p-6 border border-white/10">
        <p className="text-white/60">暫無內容，請先從 Pipeline 觸發貼文分析。</p>
      </div>
    </div>
  );
}
