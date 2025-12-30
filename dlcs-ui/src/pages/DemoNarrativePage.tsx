type MockComment = {
  id: string;
  text: string;
  like_count: number;
  cluster_id: number;
};

export default function DemoNarrativePage() {
  const mockPost = {
    id: "demo-001",
    author: "demo_user",
    timestamp: "2025-01-01T12:00:00Z",
    text: "科技巨頭推出新 AI 政策，引發創作者收入與版權的雙重焦慮。",
    like_count: 1720,
    view_count: 51500,
    reply_count: 64,
  };

  const mockComments: MockComment[] = [
    { id: "c1", text: "這政策只會讓小創作者更難生存吧？", like_count: 120, cluster_id: 0 },
    { id: "c2", text: "平台抽成又要提高了，別說是保護用戶。", like_count: 96, cluster_id: 0 },
    { id: "c3", text: "其實 AI 生成也需要人類審核，別太恐慌。", like_count: 60, cluster_id: 1 },
    { id: "c4", text: "我反而覺得這是洗牌的機會，好的內容會被看見。", like_count: 44, cluster_id: 1 },
    { id: "c5", text: "誰能告訴我版權分潤怎麼算？沒有透明度。", like_count: 33, cluster_id: 2 },
    { id: "c6", text: "法律跟不上技術，先行者優勢太大了。", like_count: 27, cluster_id: 2 },
  ];

  const phenomenon = {
    name: "AI 平台治理焦慮",
    evidence: [mockComments[0], mockComments[1]],
  };

  return (
    <div className="p-8 space-y-6">
      <h2 className="text-2xl font-bold">Demo Narrative</h2>

      {/* Anchor Post Card */}
      <div className="glass-panel rounded-xl border border-white/10 p-5">
        <div className="flex justify-between items-start">
          <div>
            <p className="text-sm text-white/60">@{mockPost.author} · {new Date(mockPost.timestamp).toLocaleString()}</p>
            <p className="text-xl font-semibold text-white mt-2">{mockPost.text}</p>
          </div>
          <div className="text-right text-white/70 text-sm">
            <div>👍 {mockPost.like_count}</div>
            <div>👁️ {mockPost.view_count}</div>
            <div>💬 {mockPost.reply_count}</div>
          </div>
        </div>
      </div>

      {/* Evidence Strip */}
      <div className="glass-panel rounded-xl border border-white/10 p-5 space-y-3">
        <h3 className="text-lg font-bold text-white">Evidence Strip</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          {mockComments.slice(0, 3).map((c) => (
            <div key={c.id} className="bg-white/5 rounded-lg p-3 border border-white/5">
              <p className="text-white/80 text-sm">{c.text}</p>
              <div className="flex justify-between text-xs text-white/50 mt-2">
                <span>👍 {c.like_count}</span>
                <span>Cluster {c.cluster_id}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Phenomenon Card */}
      <div className="glass-panel rounded-xl border border-white/10 p-5 space-y-3">
        <h3 className="text-lg font-bold text-white">Phenomenon</h3>
        <p className="text-white/80">{phenomenon.name}</p>
        <div className="space-y-2">
          {phenomenon.evidence.map((ev) => (
            <div key={ev.id} className="bg-white/5 rounded-lg p-3 border border-white/5">
              <p className="text-white/80 text-sm">{ev.text}</p>
              <div className="flex justify-between text-xs text-white/50 mt-2">
                <span>👍 {ev.like_count}</span>
                <span>Cluster {ev.cluster_id}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
