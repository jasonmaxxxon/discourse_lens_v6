import { ReactNode } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import clsx from "clsx";

type MainLayoutProps = {
  children: ReactNode;
};

const navItems: Array<{
  label: string;
  path: string;
  icon: string;
  disabled?: boolean;
}> = [
  { label: "System Vitals", path: "/ops/vitals", icon: "activity_zone" },
  { label: "Logistics (All)", path: "/ops/jobs", icon: "conveyor_belt" },
  { label: "Pipeline A", path: "/pipeline/a", icon: "view_stream" },
  { label: "Pipeline B", path: "/ops/jobs?pipeline=B", icon: "view_stream" },
  { label: "Pipeline C", path: "/ops/jobs?pipeline=C", icon: "view_stream" },
  { label: "History", path: "/history", icon: "history", disabled: true },
  { label: "Archive", path: "/archive", icon: "inventory_2", disabled: true },
];

function isActiveNav(itemPath: string, pathname: string, search: string) {
  // Query-driven items must match FULL URL.
  if (itemPath.includes("?")) return pathname + search === itemPath;

  // Logistics (All) is active ONLY when /ops/jobs AND no pipeline filter.
  if (itemPath === "/ops/jobs") {
    const sp = new URLSearchParams(search);
    return pathname === "/ops/jobs" && !sp.get("pipeline");
    }

  // Normal route match.
  return pathname === itemPath;
}

export default function MainLayout({ children }: MainLayoutProps) {
  const navigate = useNavigate();
  const location = useLocation();

  const pathname = location.pathname;
  const search = location.search;

  return (
    <div className="min-h-screen flex bg-slate-50">
      <aside className="w-64 bg-white border-r border-slate-200 fixed h-full z-30 flex flex-col">
        <div className="h-16 flex items-center px-6 border-b border-slate-100">
          <div className="flex items-center gap-2">
            <div className="size-8 bg-blue-600 text-white rounded-lg flex items-center justify-center">
              <span className="material-symbols-outlined text-[20px]">hub</span>
            </div>
            <span className="font-bold text-lg">DiscourseLens</span>
          </div>
        </div>

        <nav className="flex-1 p-4 space-y-1 overflow-y-auto">
          {navItems.map((item) => {
            const active = isActiveNav(item.path, pathname, search);

            return (
              <button
                key={item.path}
                onClick={() => {
                  if (item.disabled) return;
                  navigate(item.path);
                }}
                disabled={item.disabled}
                className={clsx(
                  "w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-all duration-200",
                  item.disabled
                    ? "opacity-40 cursor-not-allowed"
                    : active
                    ? "bg-blue-50 text-blue-700 ring-1 ring-blue-200 shadow-sm"
                    : "text-slate-600 hover:bg-slate-50 hover:text-slate-900"
                )}
              >
                <span
                  className={clsx(
                    "material-symbols-outlined text-[20px]",
                    active ? "text-blue-600" : "text-slate-400"
                  )}
                >
                  {item.icon}
                </span>
                {item.label}
              </button>
            );
          })}
        </nav>
      </aside>

      <main className="flex-1 ml-64 min-h-screen">{children}</main>
    </div>
  );
}
