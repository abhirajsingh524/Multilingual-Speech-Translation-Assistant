// =============================================================================
// Sidebar — White bg, Sky Blue active, Asmani hover
// =============================================================================
import React from "react";

const NAV_ITEMS = [
  {
    icon: (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none"
           stroke="currentColor" strokeWidth="2" strokeLinecap="round">
        <rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/>
        <rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/>
      </svg>
    ),
    label: "Overview",
    active: false,
  },
  {
    icon: (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none"
           stroke="currentColor" strokeWidth="2" strokeLinecap="round">
        <rect x="3" y="4" width="18" height="16" rx="2"/>
        <line x1="3" y1="9" x2="21" y2="9"/>
        <line x1="8" y1="4" x2="8" y2="9"/>
        <line x1="16" y1="4" x2="16" y2="9"/>
      </svg>
    ),
    label: "Timeline",
    active: true,
  },
  {
    icon: (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none"
           stroke="currentColor" strokeWidth="2" strokeLinecap="round">
        <path d="M9 11l3 3L22 4"/>
        <path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/>
      </svg>
    ),
    label: "Tasks",
    active: false,
  },
  {
    icon: (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none"
           stroke="currentColor" strokeWidth="2" strokeLinecap="round">
        <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
        <circle cx="9" cy="7" r="4"/>
        <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
        <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
      </svg>
    ),
    label: "Team",
    active: false,
  },
  {
    icon: (
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none"
           stroke="currentColor" strokeWidth="2" strokeLinecap="round">
        <line x1="18" y1="20" x2="18" y2="10"/>
        <line x1="12" y1="20" x2="12" y2="4"/>
        <line x1="6"  y1="20" x2="6"  y2="14"/>
      </svg>
    ),
    label: "Reports",
    active: false,
  },
];

export default function Sidebar({ open }) {
  return (
    <aside
      className="fixed top-[62px] left-0 h-[calc(100vh-62px)] z-40
                 transition-all duration-300 ease-in-out overflow-hidden"
      style={{
        width: open ? "220px" : "0px",
        background: "#fff",
        borderRight: "1px solid #c8e9f7",
        boxShadow: open ? "2px 0 12px rgba(79,195,247,.12)" : "none",
      }}
      aria-label="Dashboard navigation"
    >
      <nav className="flex flex-col gap-1 p-3 pt-4">
        {NAV_ITEMS.map((item) => (
          <button
            key={item.label}
            aria-label={item.label}
            className="flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm
                       font-medium transition-all duration-200 whitespace-nowrap
                       w-full text-left"
            style={item.active ? {
              background: "#e1f5fe",
              color: "#0288d1",
              fontWeight: 700,
              borderLeft: "3px solid #4FC3F7",
              paddingLeft: "9px",
            } : {
              color: "#374151",
              background: "transparent",
            }}
            onMouseEnter={e => {
              if (!item.active) {
                e.currentTarget.style.background = "#f0faff";
                e.currentTarget.style.color = "#0288d1";
                e.currentTarget.style.transform = "translateX(3px)";
              }
            }}
            onMouseLeave={e => {
              if (!item.active) {
                e.currentTarget.style.background = "transparent";
                e.currentTarget.style.color = "#374151";
                e.currentTarget.style.transform = "translateX(0)";
              }
            }}
          >
            <span style={{ color: item.active ? "#4FC3F7" : "inherit", flexShrink: 0 }}>
              {item.icon}
            </span>
            <span className={`transition-opacity duration-200 ${open ? "opacity-100" : "opacity-0"}`}>
              {item.label}
            </span>
            {item.active && open && (
              <span className="ml-auto w-2 h-2 rounded-full"
                    style={{ background: "#4FC3F7" }} aria-hidden="true"/>
            )}
          </button>
        ))}
      </nav>

      {/* Bottom — project summary card */}
      {open && (
        <div className="absolute bottom-6 left-3 right-3">
          <div className="rounded-xl p-3"
               style={{ background: "#e8f6fc", border: "1px solid #c8e9f7" }}>
            <p className="text-xs font-bold uppercase tracking-wider"
               style={{ color: "#0288d1" }}>
              Active Projects
            </p>
            <p className="text-2xl font-extrabold mt-0.5 tracking-tight"
               style={{ color: "#0288d1" }}>
              3
            </p>
            <div className="mt-2 h-1.5 rounded-full overflow-hidden"
                 style={{ background: "#bae6fd" }}>
              <div className="h-full rounded-full"
                   style={{ width: "75%", background: "#4FC3F7" }}/>
            </div>
            <p className="text-[10px] mt-1" style={{ color: "#29b6f6" }}>
              75% on schedule
            </p>
          </div>
        </div>
      )}
    </aside>
  );
}
