// =============================================================================
// DashboardHeader — Asmani bg filters, Red CTA, Sky labels
// =============================================================================
import React from "react";
import { PROJECTS, STATUS_OPTIONS } from "../data/projects";

const inputStyle = {
  padding: "9px 13px",
  borderRadius: "10px",
  border: "1.5px solid #c8e9f7",
  background: "#fff",
  color: "#111827",
  fontSize: "0.875rem",
  outline: "none",
  transition: "border-color 0.2s, box-shadow 0.2s",
  width: "100%",
};

export default function DashboardHeader({ filters, setFilters }) {
  const set = (key) => (e) => setFilters((f) => ({ ...f, [key]: e.target.value }));

  return (
    <div className="mb-6">
      {/* Title row */}
      <div className="flex flex-wrap items-start justify-between gap-4 mb-5">
        <div>
          <p className="text-xs font-bold uppercase tracking-widest mb-1"
             style={{ color: "#0288d1" }}>
            Project Management
          </p>
          <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight leading-none"
              style={{ color: "#111827" }}>
            Timeline Dashboard
          </h1>
          <p className="text-sm mt-1.5" style={{ color: "#6B7280" }}>
            Track progress, deadlines, and milestones across all projects.
          </p>
        </div>

        {/* CTA — Red */}
        <button
          className="flex items-center gap-2 px-5 py-2.5 rounded-xl font-bold text-sm
                     whitespace-nowrap transition-all duration-200
                     hover:-translate-y-0.5 hover:scale-[1.02] active:scale-[.97]"
          style={{
            background: "#EF4444",
            color: "#fff",
            boxShadow: "0 4px 14px rgba(239,68,68,.35)",
          }}
          onMouseEnter={e => e.currentTarget.style.background = "#dc2626"}
          onMouseLeave={e => e.currentTarget.style.background = "#EF4444"}
        >
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none"
               stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
            <line x1="12" y1="5" x2="12" y2="19"/>
            <line x1="5" y1="12" x2="19" y2="12"/>
          </svg>
          New Task
        </button>
      </div>

      {/* Filter bar — white card, Asmani border */}
      <div className="flex flex-wrap gap-3 p-4 rounded-2xl"
           style={{
             background: "#fff",
             border: "1px solid #c8e9f7",
             boxShadow: "0 2px 8px rgba(79,195,247,.1)",
           }}>

        {/* Date From */}
        <div className="flex flex-col gap-1 min-w-[130px]">
          <label className="text-[10px] font-bold uppercase tracking-wider"
                 style={{ color: "#0288d1" }}>
            From
          </label>
          <input
            type="date"
            value={filters.dateFrom}
            onChange={set("dateFrom")}
            style={inputStyle}
            onFocus={e => { e.target.style.borderColor = "#4FC3F7"; e.target.style.boxShadow = "0 0 0 3px rgba(79,195,247,.18)"; }}
            onBlur={e => { e.target.style.borderColor = "#c8e9f7"; e.target.style.boxShadow = "none"; }}
          />
        </div>

        {/* Date To */}
        <div className="flex flex-col gap-1 min-w-[130px]">
          <label className="text-[10px] font-bold uppercase tracking-wider"
                 style={{ color: "#0288d1" }}>
            To
          </label>
          <input
            type="date"
            value={filters.dateTo}
            onChange={set("dateTo")}
            style={inputStyle}
            onFocus={e => { e.target.style.borderColor = "#4FC3F7"; e.target.style.boxShadow = "0 0 0 3px rgba(79,195,247,.18)"; }}
            onBlur={e => { e.target.style.borderColor = "#c8e9f7"; e.target.style.boxShadow = "none"; }}
          />
        </div>

        {/* Divider */}
        <div className="w-px self-stretch hidden sm:block"
             style={{ background: "#c8e9f7" }} aria-hidden="true"/>

        {/* Project */}
        <div className="flex flex-col gap-1 min-w-[160px]">
          <label className="text-[10px] font-bold uppercase tracking-wider"
                 style={{ color: "#0288d1" }}>
            Project
          </label>
          <select
            value={filters.project}
            onChange={set("project")}
            style={{ ...inputStyle, cursor: "pointer", appearance: "none" }}
            onFocus={e => { e.target.style.borderColor = "#4FC3F7"; e.target.style.boxShadow = "0 0 0 3px rgba(79,195,247,.18)"; }}
            onBlur={e => { e.target.style.borderColor = "#c8e9f7"; e.target.style.boxShadow = "none"; }}
          >
            {PROJECTS.map((p) => (
              <option key={p.id} value={p.id}>{p.label}</option>
            ))}
          </select>
        </div>

        {/* Status */}
        <div className="flex flex-col gap-1 min-w-[150px]">
          <label className="text-[10px] font-bold uppercase tracking-wider"
                 style={{ color: "#0288d1" }}>
            Status
          </label>
          <select
            value={filters.status}
            onChange={set("status")}
            style={{ ...inputStyle, cursor: "pointer", appearance: "none" }}
            onFocus={e => { e.target.style.borderColor = "#4FC3F7"; e.target.style.boxShadow = "0 0 0 3px rgba(79,195,247,.18)"; }}
            onBlur={e => { e.target.style.borderColor = "#c8e9f7"; e.target.style.boxShadow = "none"; }}
          >
            {STATUS_OPTIONS.map((s) => (
              <option key={s.id} value={s.id}>{s.label}</option>
            ))}
          </select>
        </div>

        {/* Reset */}
        <div className="flex flex-col justify-end">
          <button
            onClick={() => setFilters({
              dateFrom: "2026-01-01",
              dateTo:   "2026-05-01",
              project:  "all",
              status:   "all",
            })}
            className="px-4 py-2 rounded-xl text-sm font-semibold
                       transition-all duration-150 hover:-translate-y-0.5"
            style={{
              background: "#e8f6fc",
              border: "1.5px solid #c8e9f7",
              color: "#0288d1",
            }}
            onMouseEnter={e => e.currentTarget.style.background = "#e1f5fe"}
            onMouseLeave={e => e.currentTarget.style.background = "#e8f6fc"}
          >
            Reset
          </button>
        </div>
      </div>
    </div>
  );
}
