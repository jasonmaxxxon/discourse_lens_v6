import { motion, useScroll, useTransform } from "framer-motion";
import { useRef, useState } from "react";
import { AnalysisJson } from "../types/analysis";
import BattlefieldCard from "./cards/BattlefieldCard";
import EngagementCard from "./cards/EngagementCard";
import RawReportCard from "./cards/RawReportCard";
import StrategyDetailCard from "./cards/StrategyDetailCard";
import ToneStrategyCard from "./cards/ToneStrategyCard";
import DiscoveryCard from "./cards/DiscoveryCard";
import QuantDiagnosticsCard from "./cards/QuantDiagnosticsCard";
import L1Card from "./cards/L1Card";
import L2Card from "./cards/L2Card";
import L3Card from "./cards/L3Card";
import { useDiscoveryData } from "../hooks/useDiscoveryData";
import { useQuantDiagnostics } from "../hooks/useQuantDiagnostics";

type Props = { data: AnalysisJson };

export const AnalysisRail = ({ data }: Props) => {
  const railRef = useRef<HTMLDivElement>(null);
  const { scrollXProgress } = useScroll({ container: railRef });
  const opacity = useTransform(scrollXProgress, [0, 1], [0.6, 1]);
  const { discovery } = useDiscoveryData(data);
  const quant = useQuantDiagnostics(data);
  const [atStart, setAtStart] = useState(true);

  const onScroll = () => {
    if (!railRef.current) return;
    setAtStart(railRef.current.scrollLeft <= 4);
  };

  return (
    <div className="relative mt-6">
      <div
        ref={railRef}
        onScroll={onScroll}
        className="flex flex-row flex-nowrap overflow-x-auto snap-x snap-mandatory gap-6 px-8 pb-8 [&::-webkit-scrollbar]:hidden"
        style={{ scrollbarWidth: "none" }}
      >
        <section className="snap-center min-w-[85vw] md:min-w-[900px] h-[75vh] flex items-stretch">
          <DiscoveryCard discovery={discovery} fallbackTitle={data.summary?.narrative_type} />
        </section>

        <section className="snap-center min-w-[85vw] md:min-w-[900px] h-[75vh] flex items-stretch">
          <ToneStrategyCard tone={data.tone} strategies={data.strategies} />
        </section>

        <section className="snap-center min-w-[85vw] md:min-w-[900px] h-[75vh] flex items-stretch">
          <BattlefieldCard battlefield={data.battlefield} />
        </section>

        <section className="snap-center min-w-[85vw] md:min-w-[900px] h-[75vh] flex items-stretch">
          <div className="flex flex-col gap-4 w-full">
            <QuantDiagnosticsCard quant={quant} />
            <EngagementCard metrics={data.metrics} />
          </div>
        </section>

        <section className="snap-center min-w-[85vw] md:min-w-[900px] h-[75vh] flex items-stretch">
          <div className="flex flex-col gap-4 w-full">
            <div className="grid gap-4 md:grid-cols-3">
              <L1Card layer={data.layers?.l1} />
              <L2Card layer={data.layers?.l2} />
              <L3Card layer={data.layers?.l3} />
            </div>
            <RawReportCard postId={data.post_id.toString()} rawMarkdown={data.raw_markdown} />
          </div>
        </section>
      </div>

      {atStart && (
        <div className="pointer-events-none absolute left-10 bottom-3 text-[11px] uppercase tracking-[0.25em] text-slate-500">
          ← Scroll / Swipe →
        </div>
      )}
    </div>
  );
};

export default AnalysisRail;
