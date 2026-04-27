// =============================================================================
// TimelineBar — rounded bars with progress fill + hover scale
// Colors: Sky=ongoing, Red=critical, Yellow=milestone, Green=completed
// =============================================================================
import React, { useCallback } from "react";
import { getBarGeometry } from "../utils/timeline";
import { TIMELINE_START, TIMELINE_END } from "../data/projects";

// Strict palette mapping
const STATUS_BAR = {
  ongoing:   { bar: "#4FC3F7", fill: "#0288d1", text: "#fff" },
  completed: { bar: "#34d399", fill: "#059669", text: "#fff" },
  critical:  { bar: "#EF4444", fill: "#dc2626", text: "#fff" },
  milestone: { bar: "#FACC15", fill: "#eab308", text: "#111827" },
};

export default function TimelineBar({ task, onHover, onLeave }) {
  const { left, width } = getBarGeometry(
    task.start, task.end, TIMELINE_START, TIMELINE_END
  );

  const colors = STATUS_BAR[task.status] || STATUS_BAR.ongoing;
  const isMilestone = task.status === "milestone";

  const handleMouseMove = useCallback((e) => {
    onHover(task, e.clientX, e.clientY);
  }, [task, onHover]);

  if (isMilestone) {
    return (
      <div
        className="absolute top-1/2 -translate-y-1/2 -translate-x-1/2 z-10 cursor-pointer"
        style={{ left: `${left}%` }}
        onMouseMove={handleMouseMove}
        onMouseLeave={onLeave}
        role="img"
        aria-label={`Milestone: ${task.name}`}
      >
        {/* Diamond shape */}
        <div
          className="w-5 h-5 rotate-45 transition-transform duration-200
                     hover:scale-125"
          style={{
            background: "#FACC15",
            border: "2px solid #eab308",
            boxShadow: "0 2px 8px rgba(250,204,21,.5)",
          }}
        />
        {/* Pulse ring */}
        <div
          className="absolute inset-0 w-5 h-5 rotate-45 animate-ping rounded-sm"
          style={{ background: "rgba(250,204,21,.3)" }}
          aria-hidden="true"
        />
      </div>
    );
  }

  return (
    <div
      className="absolute top-1/2 -translate-y-1/2 rounded-full cursor-pointer
                 overflow-hidden transition-all duration-300
                 hover:-translate-y-[55%] hover:scale-y-110"
      style={{
        left: `${left}%`,
        width: `${width}%`,
        minWidth: "6px",
        height: "26px",
        background: colors.bar,
        opacity: 0.85,
        boxShadow: `0 2px 8px ${colors.bar}55`,
      }}
      onMouseMove={handleMouseMove}
      onMouseLeave={onLeave}
      onMouseEnter={e => {
        e.currentTarget.style.opacity = "1";
        e.currentTarget.style.boxShadow = `0 4px 16px ${colors.bar}88`;
      }}
      onMouseOut={e => {
        e.currentTarget.style.opacity = "0.85";
        e.currentTarget.style.boxShadow = `0 2px 8px ${colors.bar}55`;
      }}
      role="img"
      aria-label={`${task.name}: ${task.progress}% complete`}
    >
      {/* Progress fill */}
      <div
        className="absolute inset-y-0 left-0 rounded-full transition-all duration-500"
        style={{
          width: `${task.progress}%`,
          background: colors.fill,
          opacity: 0.9,
        }}
        aria-hidden="true"
      />

      {/* Shimmer overlay */}
      <div
        className="absolute inset-0 rounded-full"
        style={{
          background: "linear-gradient(90deg, transparent 0%, rgba(255,255,255,.2) 50%, transparent 100%)",
        }}
        aria-hidden="true"
      />

      {/* Progress % label */}
      {width > 6 && (
        <span
          className="absolute inset-0 flex items-center justify-center
                     text-[9px] font-bold drop-shadow"
          style={{ color: colors.text, opacity: 0.9 }}
        >
          {task.progress}%
        </span>
      )}
    </div>
  );
}
