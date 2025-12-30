import { useState } from "react";
import { CardShell } from "./CardShell";
import { PostAnalysis } from "../../types/analysis";
import { motion, AnimatePresence } from "framer-motion";

type Props = { data: PostAnalysis };

export const AcademicReferenceCard = ({ data }: Props) => {
  const [openIndex, setOpenIndex] = useState<number | null>(null);
  return (
    <CardShell title="Academic References" subtitle="想學更多" accent="pink">
      <div className="space-y-2 text-sm">
        {data.section1.academicReferences.map((ref, idx) => (
          <div key={ref.author + ref.year} className="rounded-xl border border-slate-800 bg-slate-900/70 p-3">
            <button
              className="flex w-full items-center justify-between text-left text-white"
              onClick={() => setOpenIndex(openIndex === idx ? null : idx)}
            >
              <span className="font-semibold">
                {ref.author} ({ref.year})
              </span>
              <span className="text-xs text-subtle">{openIndex === idx ? "收起" : "點擊展開"}</span>
            </button>
            <AnimatePresence initial={false}>
              {openIndex === idx && (
                <motion.p
                  initial={{ opacity: 0, y: -4 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -4 }}
                  className="mt-2 text-subtle"
                >
                  {ref.note}
                </motion.p>
              )}
            </AnimatePresence>
          </div>
        ))}
      </div>
    </CardShell>
  );
};

export default AcademicReferenceCard;
