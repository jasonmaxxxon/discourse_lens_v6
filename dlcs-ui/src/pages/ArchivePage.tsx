import { useEffect, useState } from "react";
import { fetchPosts } from "../api/analysis";
import { FeedItem } from "../types/analysis";
import { useSimpleRouter } from "../hooks/useSimpleRouter";

export default function ArchivePage() {
  const [items, setItems] = useState<FeedItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { navigate } = useSimpleRouter();

  useEffect(() => {
    setLoading(true);
    fetchPosts()
      .then((rows) => {
        setItems(rows);
        setLoading(false);
      })
      .catch((e) => {
        const msg = e instanceof Error ? e.message : String(e);
        setError(msg);
        setLoading(false);
      });
  }, []);

  return (
    <div className="p-8 space-y-4">
      <h2 className="text-2xl font-bold">Archive</h2>
      <p className="text-white/70">已分析貼文清單，可點入敘事詳情。</p>
      {loading && <p className="text-white/60">載入中…</p>}
      {error && <p className="text-red-400 text-sm">{error}</p>}
      <div className="glass-panel rounded-xl p-0 border border-white/10 overflow-hidden">
        <table className="min-w-full text-sm">
          <thead className="bg-white/5 text-white/70 uppercase tracking-wide text-xs">
            <tr>
              <th className="text-left px-4 py-3">Post ID</th>
              <th className="text-left px-4 py-3">Snippet</th>
              <th className="text-left px-4 py-3">Author</th>
              <th className="text-left px-4 py-3">Likes/Views/Replies</th>
              <th className="text-left px-4 py-3">分析狀態</th>
              <th className="text-left px-4 py-3">封存</th>
            </tr>
          </thead>
          <tbody>
            {items.map((item) => (
              <tr
                key={item.id}
                className="border-t border-white/5 hover:bg-white/5 cursor-pointer"
                onClick={() => navigate(`/narrative/${item.id}`)}
              >
                <td className="px-4 py-3 text-white">{item.id}</td>
                <td className="px-4 py-3 text-white/80 max-w-xs truncate">{item.snippet}</td>
                <td className="px-4 py-3 text-white/70">{item.author || "未知"}</td>
                <td className="px-4 py-3 text-white/70">
                  {item.likeCount ?? 0} / {item.viewCount ?? 0} / {item.replyCount ?? 0}
                </td>
                <td className="px-4 py-3">
                  {item.hasAnalysis ? (
                    <span className="text-green-300 text-xs bg-green-500/10 px-2 py-1 rounded-full">已分析</span>
                  ) : (
                    <span className="text-yellow-300 text-xs bg-yellow-500/10 px-2 py-1 rounded-full">需重跑分析</span>
                  )}
                  {item.hasAnalysis && item.analysisIsValid === false && (
                    <div className="text-yellow-300 text-xs mt-1">分析無效，需重跑</div>
                  )}
                </td>
                <td className="px-4 py-3">
                  {item.hasArchive ? (
                    <span className="text-green-300 text-xs bg-green-500/10 px-2 py-1 rounded-full">已封存</span>
                  ) : (
                    <span className="text-white/60 text-xs bg-white/5 px-2 py-1 rounded-full">未封存</span>
                  )}
                </td>
              </tr>
            ))}
            {!loading && items.length === 0 && (
              <tr>
                <td className="px-4 py-6 text-white/60 text-center" colSpan={6}>
                  尚無貼文，請先執行 Pipeline。
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
