// =============================================================================
// Timeline utility helpers
// =============================================================================

export function getBarGeometry(taskStart, taskEnd, windowStart, windowEnd) {
  const total   = windowEnd - windowStart;
  const startMs = Math.max(new Date(taskStart) - windowStart, 0);
  const endMs   = Math.min(new Date(taskEnd)   - windowStart, total);
  const left    = (startMs / total) * 100;
  const width   = Math.max(((endMs - startMs) / total) * 100, 0.4);
  return { left, width };
}

export function getMonthLabels(windowStart, windowEnd) {
  const labels = [];
  const cursor = new Date(windowStart.getFullYear(), windowStart.getMonth(), 1);
  const total  = windowEnd - windowStart;
  while (cursor <= windowEnd) {
    const left = ((cursor - windowStart) / total) * 100;
    labels.push({
      label: cursor.toLocaleString("default", { month: "short", year: "2-digit" }),
      left,
    });
    cursor.setMonth(cursor.getMonth() + 1);
  }
  return labels;
}

export function getTodayOffset(windowStart, windowEnd) {
  const today = new Date();
  if (today < windowStart || today > windowEnd) return null;
  return ((today - windowStart) / (windowEnd - windowStart)) * 100;
}

export function fmtDate(dateStr) {
  return new Date(dateStr).toLocaleDateString("en-US", {
    month: "short", day: "numeric", year: "numeric",
  });
}
