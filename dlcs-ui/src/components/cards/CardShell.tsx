import { PropsWithChildren } from "react";
import { motion } from "framer-motion";
import clsx from "clsx";

export type CardShellProps = PropsWithChildren<{
  title: string;
  subtitle?: string;
  accent?: "cyan" | "amber" | "pink";
  className?: string;
}>;

const accentMap: Record<string, string> = {
  cyan: "from-cyan-500/30 to-cyan-400/10 border-cyan-500/40",
  amber: "from-amber-400/40 to-amber-300/10 border-amber-400/40",
  pink: "from-pink-500/40 to-pink-400/10 border-pink-500/40",
};

export const CardShell = ({
  title,
  subtitle,
  accent = "cyan",
  className,
  children,
}: CardShellProps) => {
  return (
    <motion.div
      className={clsx(
        "relative w-full rounded-3xl border-2 border-slate-700 bg-slate-950/90 p-6 md:p-8",
        "shadow-[4px_4px_0px_0px_rgba(148,163,184,0.6)]",
        "text-white",
        "transition-all duration-200",
        className
      )}
      whileHover={{ translateY: -2 }}
      initial={{ opacity: 0, y: 12 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
    >
      <div className="relative flex flex-col gap-2">
        <div>
          <h3 className="text-lg font-semibold tracking-[0.18em] uppercase text-slate-100">{title}</h3>
          {subtitle && <p className="text-sm text-slate-400 italic">{subtitle}</p>}
        </div>
        {children}
      </div>
    </motion.div>
  );
};

export default CardShell;
