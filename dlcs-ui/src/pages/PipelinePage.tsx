export default function PipelinePage({ variant }: { variant: string }) {
  return (
    <div className="min-h-screen bg-[#0f172a] text-white p-8">
      <h1 className="text-3xl font-bold mb-4">Pipeline {variant}</h1>
      <div className="p-6 rounded-xl border border-white/10 bg-white/5">
        <p className="text-slate-400">Legacy Pipeline Controller (not migrated yet)</p>
      </div>
    </div>
  );
}
