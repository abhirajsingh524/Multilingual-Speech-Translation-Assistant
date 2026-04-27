// =============================================================================
// Navbar — Sky Blue (#4FC3F7) background, white text
// =============================================================================
import React from "react";

export default function Navbar({ sidebarOpen, setSidebarOpen }) {
  return (
    <header
      className="sticky top-0 z-50 flex items-center justify-between px-6"
      style={{
        height: "62px",
        background: "#4FC3F7",
        borderBottom: "1px solid rgba(255,255,255,.15)",
        boxShadow: "0 2px 16px rgba(79,195,247,.35)",
      }}
    >
      {/* Left — hamburger + logo */}
      <div className="flex items-center gap-3">
        <button
          onClick={() => setSidebarOpen(o => !o)}
          aria-label="Toggle sidebar"
          className="w-9 h-9 rounded-xl flex items-center justify-center
                     transition-all duration-150 hover:scale-105"
          style={{
            background: "rgba(255,255,255,.15)",
            border: "1.5px solid rgba(255,255,255,.3)",
            color: "#fff",
          }}
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none"
               stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
            <line x1="3" y1="6"  x2="21" y2="6"/>
            <line x1="3" y1="12" x2="21" y2="12"/>
            <line x1="3" y1="18" x2="21" y2="18"/>
          </svg>
        </button>

        {/* Logo mark — white square with sky icon */}
        <div className="w-8 h-8 rounded-xl flex items-center justify-center shadow-md"
             style={{ background: "#fff" }}>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none"
               stroke="#0288d1" strokeWidth="2" strokeLinecap="round">
            <rect x="3" y="4" width="18" height="16" rx="2"/>
            <line x1="3"  y1="9"  x2="21" y2="9"/>
            <line x1="8"  y1="4"  x2="8"  y2="9"/>
            <line x1="16" y1="4"  x2="16" y2="9"/>
          </svg>
        </div>

        <div>
          <span className="font-extrabold text-base tracking-tight leading-none"
                style={{ color: "#fff" }}>
            ProjectFlow
          </span>
          <span className="block text-[10px] font-medium leading-none mt-0.5"
                style={{ color: "rgba(255,255,255,.7)" }}>
            Timeline Dashboard
          </span>
        </div>
      </div>

      {/* Right — actions + avatar */}
      <div className="flex items-center gap-2">

        {/* Notification bell — Yellow dot */}
        <button aria-label="Notifications"
                className="relative w-9 h-9 rounded-xl flex items-center justify-center
                           transition-all duration-150 hover:scale-105"
                style={{
                  background: "rgba(255,255,255,.12)",
                  border: "1.5px solid rgba(255,255,255,.25)",
                  color: "#fff",
                }}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none"
               stroke="currentColor" strokeWidth="2" strokeLinecap="round">
            <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/>
            <path d="M13.73 21a2 2 0 0 1-3.46 0"/>
          </svg>
          {/* Yellow notification dot */}
          <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full border"
                style={{ background: "#FACC15", borderColor: "#4FC3F7" }}
                aria-hidden="true"/>
        </button>

        {/* Settings */}
        <button aria-label="Settings"
                className="w-9 h-9 rounded-xl flex items-center justify-center
                           transition-all duration-150 hover:scale-105"
                style={{
                  background: "rgba(255,255,255,.12)",
                  border: "1.5px solid rgba(255,255,255,.25)",
                  color: "#fff",
                }}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none"
               stroke="currentColor" strokeWidth="2" strokeLinecap="round">
            <circle cx="12" cy="12" r="3"/>
            <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/>
          </svg>
        </button>

        {/* Divider */}
        <div className="w-px h-6 mx-1" style={{ background: "rgba(255,255,255,.25)" }}
             aria-hidden="true"/>

        {/* User avatar — Yellow initial */}
        <button aria-label="User profile"
                className="flex items-center gap-2 px-2 py-1 rounded-xl
                           transition-all duration-150 hover:scale-105"
                style={{ background: "rgba(255,255,255,.1)" }}>
          <div className="w-8 h-8 rounded-full flex items-center justify-center
                          font-bold text-sm shadow"
               style={{ background: "#FACC15", color: "#111827" }}>
            A
          </div>
          <div className="hidden sm:block text-left">
            <p className="text-xs font-semibold leading-none" style={{ color: "#fff" }}>
              Anoop K.
            </p>
            <p className="text-[10px] leading-none mt-0.5" style={{ color: "rgba(255,255,255,.65)" }}>
              Admin
            </p>
          </div>
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none"
               stroke="rgba(255,255,255,.7)" strokeWidth="2.5" strokeLinecap="round">
            <path d="M6 9l6 6 6-6"/>
          </svg>
        </button>
      </div>
    </header>
  );
}
