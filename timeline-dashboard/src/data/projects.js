// =============================================================================
// Project Timeline — Sample Data
// =============================================================================

export const PROJECTS = [
  { id: "all",   label: "All Projects" },
  { id: "alpha", label: "Project Alpha" },
  { id: "beta",  label: "Project Beta" },
  { id: "gamma", label: "Project Gamma" },
];

export const STATUS_OPTIONS = [
  { id: "all",       label: "All Status" },
  { id: "ongoing",   label: "Ongoing" },
  { id: "completed", label: "Completed" },
  { id: "critical",  label: "Critical" },
  { id: "milestone", label: "Milestone" },
];

export const TASKS = [
  { id: 1,  project: "alpha", name: "Requirements Gathering", category: "Design",      status: "completed", start: "2026-01-05", end: "2026-01-18", progress: 100, assignee: "Priya S." },
  { id: 2,  project: "alpha", name: "UI/UX Wireframes",       category: "Design",      status: "completed", start: "2026-01-15", end: "2026-02-01", progress: 100, assignee: "Rahul M." },
  { id: 3,  project: "alpha", name: "Frontend Development",   category: "Engineering", status: "ongoing",   start: "2026-02-01", end: "2026-03-15", progress: 68,  assignee: "Anoop K." },
  { id: 4,  project: "alpha", name: "Backend API",            category: "Engineering", status: "ongoing",   start: "2026-02-10", end: "2026-03-20", progress: 52,  assignee: "Sara T." },
  { id: 5,  project: "alpha", name: "Alpha Release",          category: "Milestone",   status: "milestone", start: "2026-03-20", end: "2026-03-20", progress: 0,   assignee: "Team" },
  { id: 6,  project: "alpha", name: "QA & Testing",           category: "QA",          status: "critical",  start: "2026-03-18", end: "2026-04-05", progress: 15,  assignee: "Dev T." },
  { id: 7,  project: "beta",  name: "Market Research",        category: "Research",    status: "completed", start: "2026-01-10", end: "2026-01-28", progress: 100, assignee: "Meera J." },
  { id: 8,  project: "beta",  name: "Architecture Design",    category: "Engineering", status: "completed", start: "2026-01-25", end: "2026-02-12", progress: 100, assignee: "Kiran P." },
  { id: 9,  project: "beta",  name: "Core Module Dev",        category: "Engineering", status: "ongoing",   start: "2026-02-12", end: "2026-04-01", progress: 44,  assignee: "Anoop K." },
  { id: 10, project: "beta",  name: "Integration Testing",    category: "QA",          status: "critical",  start: "2026-03-25", end: "2026-04-10", progress: 5,   assignee: "Dev T." },
  { id: 11, project: "beta",  name: "Beta Launch",            category: "Milestone",   status: "milestone", start: "2026-04-15", end: "2026-04-15", progress: 0,   assignee: "Team" },
  { id: 12, project: "gamma", name: "Concept Validation",     category: "Research",    status: "completed", start: "2026-02-01", end: "2026-02-20", progress: 100, assignee: "Priya S." },
  { id: 13, project: "gamma", name: "Prototype Build",        category: "Engineering", status: "ongoing",   start: "2026-02-20", end: "2026-03-28", progress: 72,  assignee: "Rahul M." },
  { id: 14, project: "gamma", name: "Stakeholder Review",     category: "Milestone",   status: "milestone", start: "2026-03-28", end: "2026-03-28", progress: 0,   assignee: "Team" },
  { id: 15, project: "gamma", name: "Production Deployment",  category: "Engineering", status: "critical",  start: "2026-04-01", end: "2026-04-20", progress: 0,   assignee: "Kiran P." },
];

export const TIMELINE_START = new Date("2026-01-01");
export const TIMELINE_END   = new Date("2026-05-01");
