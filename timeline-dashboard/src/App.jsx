// =============================================================================
// App — Dashboard container
// Palette: Asmani #87CEEB · Sky #4FC3F7 · Red #EF4444 · Yellow #FACC15
//          White #FFFFFF · Dark #111827
// =============================================================================
import React, { useState, useMemo } from "react";
import Navbar from "./components/Navbar";
import Sidebar from "./components/Sidebar";
import DashboardHeader from "./components/DashboardHeader";
import StatsBar from "./components/StatsBar";
import GanttChart from "./components/GanttChart";
import { TASKS } from "./data/projects";

const DEFAULT_FILTERS = {
  dateFrom: "2026-01-01",
  dateTo:   "2026-05-01",
  project:  "all",
  status:   "all",
};

export default function App() {
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [filters, setFilters] = useState(DEFAULT_FILTERS);

  const filteredTasks = useMemo(() => {
    return TASKS.filter((t) => {
      if (filters.project !== "all" && t.project !== filters.project) return false;
      if (filters.status  !== "all" && t.status  !== filters.status)  return false;
      const from = new Date(filters.dateFrom);
      const to   = new Date(filters.dateTo);
      const ts   = new Date(t.start);
      const te   = new Date(t.end);
      if (te < from || ts > to) return false;
      return true;
    });
  }, [filters]);

  return (
    <div className="min-h-screen" style={{ background: "#e8f6fc", fontFamily: "'Inter', system-ui, sans-serif" }}>
      {/* Navbar */}
      <Navbar sidebarOpen={sidebarOpen} setSidebarOpen={setSidebarOpen} />

      <div className="flex">
        {/* Sidebar */}
        <Sidebar open={sidebarOpen} />

        {/* Main content */}
        <main
          id="main-content"
          className="flex-1 min-w-0 transition-all duration-300"
          style={{ marginLeft: sidebarOpen ? "220px" : "0" }}
        >
          <div className="max-w-[1280px] mx-auto px-4 sm:px-6 py-8">

            {/* Header + filters */}
            <DashboardHeader filters={filters} setFilters={setFilters} />

            {/* KPI stats */}
            <StatsBar tasks={filteredTasks} />

            {/* Gantt chart card */}
            <div
              className="rounded-2xl p-6"
              style={{
                background: "#fff",
                border: "1px solid #c8e9f7",
                boxShadow: "0 4px 16px rgba(79,195,247,.12)",
                animation: "fadeIn 350ms ease both",
              }}
            >
              <style>{`
                @keyframes fadeIn {
                  from { opacity: 0; transform: translateY(12px); }
                  to   { opacity: 1; transform: translateY(0); }
                }
              `}</style>

              <div className="flex items-center justify-between mb-5">
                <div>
                  <h2 className="text-base font-bold tracking-tight"
                      style={{ color: "#111827" }}>
                    Project Timeline
                  </h2>
                  <p className="text-xs mt-0.5" style={{ color: "#9CA3AF" }}>
                    {filteredTasks.length} task{filteredTasks.length !== 1 ? "s" : ""} shown
                    &nbsp;·&nbsp; Jan 2026 – May 2026
                  </p>
                </div>

                {/* View toggle */}
                <div className="flex items-center gap-1 p-1 rounded-xl"
                     style={{ background: "#e8f6fc", border: "1px solid #c8e9f7" }}>
                  {["Gantt", "List", "Board"].map((v, i) => (
                    <button
                      key={v}
                      className="px-3 py-1.5 rounded-lg text-xs font-semibold
                                 transition-all duration-150"
                      style={i === 0 ? {
                        background: "#fff",
                        color: "#0288d1",
                        border: "1px solid #bae6fd",
                        boxShadow: "0 1px 4px rgba(79,195,247,.15)",
                      } : {
                        color: "#9CA3AF",
                        background: "transparent",
                      }}
                    >
                      {v}
                    </button>
                  ))}
                </div>
              </div>

              <GanttChart tasks={filteredTasks} />
            </div>

            {/* Footer note */}
            <p className="text-center text-xs mt-8" style={{ color: "#9CA3AF" }}>
              © 2026 ProjectFlow · Built with React &amp; Tailwind CSS
            </p>
          </div>
        </main>
      </div>
    </div>
  );
}
