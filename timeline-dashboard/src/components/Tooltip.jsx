// =============================================================================
// Tooltip — white card, Sky border, colored status badge
// =============================================================================
import React from "react";
import { fmtDate } from "../utils/timeline";

const STATUS_CONFIG = {
  ongoing:   { bg: "#e1f5fe", color: "#0288d1", dot: "#4FC3F7", label: "Ongoing" },
  completed: { bg: "#f0fdf4", color: "#065f46", dot: "#34d399", label: "Completed" },
  critical:  { bg: "#fef2f2", color: "#dc2626", dot: "#EF4444", label: "Critical" },
  milestone: { bg: "#fefce8", color: "#92400e", dot: "#FACC15", label: "Milestone" },
};

export default function Tooltip({ task, x, y, visible }) {
  if (!visible || !task) return null;

  const cfg = STATUS_CONFIG[task.status] || STATUS_CONFIG.ongoing;

  return (
    <div
      role="tooltip"
      aria-live="polite"
      style={{
        position:      "fixed",
        left:          Math.min(x + 14, window.innerWidth - 248),
        top:           y - 10,
        zIndex:        9999,
        pointerEvents: "none",
        width:         "228px",
        background:    "#fff",
        border:        "1px solid #c8e9f7",
        borderRadius:  "16px",
        padding:       "16px",
        boxShadow:     "0 8px 32px rgba(79,195,247,.2), 0 2px 8px rgba(79,195,247,.1)",
        animation:     "tooltipIn 200ms ease both",
      }}
    >
      <style>{`
        @keyframes tooltipIn {
          from { opacity: 0; transform: translateY(6px) scale(.97); }
          to   { opacity: 1; transform: translateY(0) scale(1); }
        }
      `}</style>

      {/* Task name */}
      <p className="font-bold text-sm leading-tight mb-2" style={{ color: "#111827" }}>
        {task.name}
      </p>

      {/* Status badge */}
      <span
        className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full
                   text-[10px] font-bold mb-3"
        style={{ background: cfg.bg, color: cfg.color, border: `1px solid ${cfg.dot}44` }}
      >
        <span className="w-1.5 h-1.5 rounded-full" style={{ background: cfg.dot }}
              aria-hidden="true"/>
        {cfg.label}
      </span>

      {/* Details */}
      <div className="space-y-1.5 text-xs" style={{ color: "#374151" }}>
        <div className="flex justify-between">
          <span style={{ color: "#9CA3AF" }}>Start</span>
          <span className="font-semibold">{fmtDate(task.start)}</span>
        </div>
        <div className="flex justify-between">
          <span style={{ color: "#9CA3AF" }}>End</span>
          <span className="font-semibold">{fmtDate(task.end)}</span>
        </div>
        <div className="flex justify-between">
          <span style={{ color: "#9CA3AF" }}>Assignee</span>
          <span className="font-semibold">{task.assignee}</span>
        </div>
      </div>

      {/* Progress bar */}
      {task.status !== "milestone" && (
        <div className="mt-3">
          <div className="flex justify-between text-[10px] mb-1">
            <span style={{ color: "#9CA3AF" }}>Progress</span>
            <span className="font-bold" style={{ color: "#0288d1" }}>
              {task.progress}%
            </span>
          </div>
          <div className="h-1.5 rounded-full overflow-hidden"
               style={{ background: "#e8f6fc" }}>
            <div
              className="h-full rounded-full transition-all duration-500"
              style={{
                width: `${task.progress}%`,
                background: cfg.dot,
              }}
            />
          </div>
        </div>
      )}
    </div>
  );
}
