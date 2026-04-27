// =============================================================================
// StatsBar — 4 KPI cards: Sky / Sky / Red / Yellow
// =============================================================================
import React from "react";

export default function StatsBar({ tasks }) {
  const total     = tasks.length;
  const ongoing   = tasks.filter((t) => t.status === "ongoing").length;
  const critical  = tasks.filter((t) => t.status === "critical").length;
  const completed = tasks.filter((t) => t.status === "completed").length;
  const milestones= tasks.filter((t) => t.status === "milestone").length;

  const cards = [
    {
      label:    "Total Tasks",
      value:    total,
      sub:      "across all projects",
      icon:     "📋",
      bg:       "#e8f6fc",
      border:   "#c8e9f7",
      numColor: "#0288d1",
      iconBg:   "#e1f5fe",
    },
    {
      label:    "Ongoing",
      value:    ongoing,
      sub:      `${total ? Math.round((ongoing / total) * 100) : 0}% of tasks`,
      icon:     "🔄",
      bg:       "#f0faff",
      border:   "#bae6fd",
      numColor: "#0288d1",
      iconBg:   "#e1f5fe",
    },
    {
      label:    "Critical",
      value:    critical,
      sub:      "need immediate attention",
      icon:     "🚨",
      bg:       "#fef2f2",
      border:   "#fecaca",
      numColor: "#dc2626",
      iconBg:   "#fee2e2",
    },
    {
      label:    "Milestones",
      value:    milestones,
      sub:      `${completed} tasks completed`,
      icon:     "🏆",
      bg:       "#fefce8",
      border:   "#fef08a",
      numColor: "#92400e",
      iconBg:   "#fef9c3",
    },
  ];

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      {cards.map((c, i) => (
        <article
          key={c.label}
          className="flex items-center gap-4 p-4 rounded-2xl
                     transition-all duration-300 cursor-default"
          style={{
            background: c.bg,
            border: `1px solid ${c.border}`,
            boxShadow: "0 2px 8px rgba(79,195,247,.08)",
            animationDelay: `${i * 60}ms`,
          }}
          onMouseEnter={e => {
            e.currentTarget.style.transform = "translateY(-4px)";
            e.currentTarget.style.boxShadow = "0 8px 24px rgba(79,195,247,.18)";
          }}
          onMouseLeave={e => {
            e.currentTarget.style.transform = "translateY(0)";
            e.currentTarget.style.boxShadow = "0 2px 8px rgba(79,195,247,.08)";
          }}
        >
          <div className="w-11 h-11 rounded-xl flex items-center justify-center
                          text-xl flex-shrink-0 shadow-sm"
               style={{ background: c.iconBg, border: `1px solid ${c.border}` }}>
            {c.icon}
          </div>
          <div className="min-w-0">
            <p className="text-2xl font-extrabold leading-none tracking-tight"
               style={{ color: c.numColor }}>
              {c.value}
            </p>
            <p className="text-xs font-semibold mt-0.5" style={{ color: "#111827" }}>
              {c.label}
            </p>
            <p className="text-[10px] mt-0.5 truncate" style={{ color: "#9CA3AF" }}>
              {c.sub}
            </p>
          </div>
        </article>
      ))}
    </div>
  );
}
