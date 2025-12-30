import { useEffect, useState } from "react";
import { fetchPosts } from "../api/analysis";
import { FeedItem } from "../types/analysis";

interface PostSelectorProps {
  selectedPostId?: string;
  onSelect: (id: string) => void;
}

const formatDate = (value?: string) => {
  if (!value) return "未知時間";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString("zh-HK", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
};

export function PostSelector({ selectedPostId, onSelect }: PostSelectorProps) {
  const [posts, setPosts] = useState<FeedItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);

    fetchPosts()
      .then((items) => {
        if (!cancelled) {
          setPosts(items);
          setLoading(false);
        }
      })
      .catch((err) => {
        if (!cancelled) {
          const msg = err instanceof Error ? err.message : String(err);
          setError(msg || "無法取得貼文清單");
          setLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!selectedPostId && posts.length > 0) {
      onSelect(posts[0].id);
    }
  }, [selectedPostId, posts, onSelect]);

  return (
    <div className="rounded-2xl border border-slate-800/80 bg-slate-900/60 p-4 shadow-lg">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm uppercase tracking-wide text-slate-400">已分析貼文</p>
          <p className="text-lg font-semibold text-white">Post Selector</p>
        </div>
        {loading && <span className="text-xs text-amber-200">Loading…</span>}
        {error && <span className="text-xs text-rose-300">Failed</span>}
      </div>

      {error && (
        <div className="mt-3 rounded-lg border border-rose-500/50 bg-rose-500/10 p-3 text-sm text-rose-100">
          無法取得貼文清單：{error}
        </div>
      )}

      {!error && (
        <div className="mt-3 space-y-3">
          {loading && (
            <div className="space-y-2">
              <div className="h-16 w-full animate-pulse rounded-xl bg-slate-800/60" />
              <div className="h-16 w-full animate-pulse rounded-xl bg-slate-800/40" />
            </div>
          )}
          {!loading && posts.length === 0 && (
            <div className="rounded-xl border border-slate-800/80 bg-slate-900/60 p-3 text-sm text-slate-300">
              尚未有完成分析的貼文。
            </div>
          )}
          {!loading &&
            posts.map((post) => {
              const isActive = post.id === selectedPostId;
              return (
                <button
                  key={post.id}
                  type="button"
                  onClick={() => onSelect(post.id)}
                  className={`w-full rounded-xl border p-3 text-left transition ${
                    isActive
                      ? "border-cyan-400/80 bg-cyan-500/10"
                      : "border-slate-800/80 bg-slate-900/60 hover:border-cyan-500/40 hover:bg-slate-800/60"
                  }`}
                >
                  <div className="flex items-center justify-between gap-3">
                    <p className="text-xs uppercase tracking-wide text-slate-400">
                      {formatDate(post.createdAt)}
                    </p>
                    {isActive && <span className="text-[10px] font-semibold text-cyan-200">Selected</span>}
                  </div>
                  <p className="mt-1 line-clamp-2 text-sm text-white">{post.snippet || "（無摘要）"}</p>
                  {post.aiTags && post.aiTags.length > 0 && (
                    <div className="mt-2 flex flex-wrap gap-1">
                      {post.aiTags.map((tag, idx) => (
                        <span
                          key={`${post.id}-tag-${idx}-${tag}`}
                          className="rounded-full bg-slate-800/80 px-2 py-0.5 text-[11px] text-slate-200"
                        >
                          {tag}
                        </span>
                      ))}
                    </div>
                  )}
                </button>
              );
            })}
        </div>
      )}
    </div>
  );
}

export default PostSelector;
