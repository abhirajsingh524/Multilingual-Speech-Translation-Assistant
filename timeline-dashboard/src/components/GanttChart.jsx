// =============================================================================
// GanttChart — Asmani bg, Sky ruler, Red today line, Yellow milestones
// =============================================================================
import React, { useState, useCallback, useRef } from "react";
import TimelineBar from "./TimelineBar";
import Tooltip from "./Tooltip";
import { getMonthLabels, getTodayOffset } from "../utils/timeline";
import { TIMELINE_START, TIMELINE_END } from "../data/projects";

const STATUS_DOT = {
  ongoing:   "#4FC3F7",
  completed: "#34d399",
  critical:  "#EF4444",
  milestone: "#FACC15",
};

const STATUS_LABEL = {
  ongoing:   "Ongoing",
  completed: "Completed",
  critical:  "Critical",
  milestone: "Milestone",
};

export default function GanttChart({ tasks }) {
  const [tooltip, setTooltip] = useState({ task: null, x: 0, y: 0, visible: false });
  const hideTimer = useRef(null);

  const handleHover = useCallback((task, x, y) => {
    clearTimeout(hideTimer.current);
    setTooltip({ task, x, y, visible: true });
  }, []);

  const handleLeave = useCallback(() => {
    hideTimer.current = setTimeout(() => {
      setTooltip((t) => ({ ...t, visible: false }));
    }, 120);
  }, []);

  const months   = getMonthLabels(TIMELINE_START, TIMELINE_END);
  const todayPct = getTodayOffset(TIMELINE_START, TIMELINE_END);

  if (!tasks.length) {
    return (
      <div className="flex flex-col items-center justify-center py-20"
           style={{ color: "#9CA3AF" }}>
        <div className="w-16 h-16 rounded-2xl flex items-center justify-center
                        text-3xl mb-4"
             style={{ background: "#e1f5fe", border: "1px solid #bae6fd" }}>
          📭
        </div>
        <p className="font-semibold" style={{ color: "#374151" }}>
          No tasks match your filters
        </p>
        <p className="text-sm mt-1">Try adjusting the date range or status filter.</p>
      </div>
    );
  }

  return (
    <div className="relative">
      {/* Scrollable container */}
      <div className="overflow-x-auto rounded-xl"
           style={{ border: "1px solid #c8e9f7" }}>
        <div style={{ minWidth: "700px" }}>

          {/* ── Month ruler — Sky Blue tint ─────────────────────────────── */}
          <div className="flex relative" style={{ height: "36px", background: "#e1f5fe", borderBottom: "1px solid #bae6fd" }}>
            {/* Label column */}
            <div className="flex-shrink-0 w-48 flex items-center px-4"
                 style={{ borderRight: "1px solid #bae6fd" }}>
              <span className="text-[10px] font-bold uppercase tracking-wider"
                    style={{ color: "#0288d1" }}>
                Task
              </span>
            </div>

            {/* Ruler */}
            <div className="flex-1 relative overflow-hidden">
              {months.map((m) => (
                <div
                  key={m.label}
                  className="absolute top-0 bottom-0 flex items-center"
                  style={{ left: `${m.left}%` }}
                >
                  <span className="text-[10px] font-semibold pl-1.5 whitespace-nowrap"
                        style={{ color: "#0288d1" }}>
                    {m.label}
                  </span>
                  <div className="absolute bottom-0 left-0 w-px h-2"
                       style={{ background: "#bae6fd" }} aria-hidden="true"/>
                </div>
              ))}
            </div>

            {/* Progress header */}
            <div className="flex-shrink-0 w-14 flex items-center justify-center"
                 style={{ borderLeft: "1px solid #bae6fd" }}>
              <span className="text-[10px] font-bold uppercase tracking-wider"
                    style={{ color: "#0288d1" }}>
                %
              </span>
            </div>
          </div>

          {/* ── Task rows ───────────────────────────────────────────────── */}
          {tasks.map((task, idx) => (
            <div
              key={task.id}
              className="flex transition-colors duration-150"
              style={{
                height: "52px",
                borderBottom: idx < tasks.length - 1 ? "1px solid #e8f6fc" : "none",
                background: idx % 2 === 0 ? "#fff" : "#f0faff",
              }}
              onMouseEnter={e => e.currentTarget.style.background = "#e8f6fc"}
              onMouseLeave={e => e.currentTarget.style.background = idx % 2 === 0 ? "#fff" : "#f0faff"}
            >
              {/* Task label column */}
              <div className="flex-shrink-0 w-48 flex items-center gap-2.5 px-4"
                   style={{ borderRight: "1px solid #e8f6fc" }}>
                <span className="w-2 h-2 rounded-full flex-shrink-0"
                      style={{ background: STATUS_DOT[task.status] || "#4FC3F7" }}
                      aria-hidden="true"/>
                <div className="min-w-0">
                  <p className="text-xs font-semibold truncate leading-tight"
                     style={{ color: "#111827" }}>
                    {task.name}
                  </p>
                  <p className="text-[10px] truncate mt-0.5" style={{ color: "#9CA3AF" }}>
                    {task.assignee}
                  </p>
                </div>
              </div>

              {/* Bar area */}
              <div className="flex-1 relative">
                {/* Subtle vertical grid lines */}
                {months.map((m) => (
                  <div
                    key={m.label}
                    className="absolute top-0 bottom-0 w-px"
                    style={{ left: `${m.left}%`, background: "rgba(135,206,235,.3)" }}
                    aria-hidden="true"
                  />
                ))}

                {/* Today line — Red */}
                {todayPct !== null && (
                  <div
                    className="absolute top-0 bottom-0 z-10"
                    style={{ left: `${todayPct}%`, width: "2px", background: "rgba(239,68,68,.7)" }}
                    aria-label="Today"
                  >
                    <div className="absolute -top-0 left-1/2 -translate-x-1/2 w-2 h-2 rounded-full"
                         style={{ background: "#EF4444" }}/>
                  </div>
                )}

                {/* The bar */}
                <TimelineBar
                  task={task}
                  onHover={handleHover}
                  onLeave={handleLeave}
                />
              </div>

              {/* Progress % column */}
              <div className="flex-shrink-0 w-14 flex items-center justify-center"
                   style={{ borderLeft: "1px solid #e8f6fc" }}>
                {task.status !== "milestone" ? (
                  <span className="text-xs font-bold"
                        style={{
                          color: task.progress === 100 ? "#059669"
                               : task.status === "critical" ? "#dc2626"
                               : "#0288d1",
                        }}>
                    {task.progress}%
                  </span>
                ) : (
                  <span className="text-base" style={{ color: "#FACC15" }}
                        aria-label="Milestone">◆</span>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Legend */}
      <div className="flex flex-wrap gap-4 mt-4 px-1">
        {Object.entries(STATUS_DOT).map(([key, color]) => (
          <div key={key} className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded-full" style={{ background: color }}
                  aria-hidden="true"/>
            <span className="text-xs font-medium" style={{ color: "#6B7280" }}>
              {STATUS_LABEL[key]}
            </span>
          </div>
        ))}
        {/* Today marker */}
        <div className="flex items-center gap-1.5">
          <span className="w-3 h-0.5 rounded-full" style={{ background: "#EF4444" }}
                aria-hidden="true"/>
          <span className="text-xs font-medium" style={{ color: "#6B7280" }}>Today</span>
        </div>
      </div>

      {/* Tooltip */}
      <Tooltip
        task={tooltip.task}
        x={tooltip.x}
        y={tooltip.y}
        visible={tooltip.visible}
      />
    </div>
  );
}
