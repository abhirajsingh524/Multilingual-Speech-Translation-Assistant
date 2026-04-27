/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx,ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        inter: ["Inter", "system-ui", "-apple-system", "sans-serif"],
      },
      colors: {
        asmani: {
          DEFAULT: "#87CEEB",
          light:   "#c8e9f7",
          xlight:  "#e8f6fc",
          dark:    "#5bb8e0",
        },
        sky: {
          DEFAULT: "#4FC3F7",
          dark:    "#29b6f6",
          deeper:  "#0288d1",
          light:   "#e1f5fe",
          xlight:  "#f0faff",
        },
      },
      boxShadow: {
        sky:      "0 4px 14px rgba(79,195,247,.4)",
        "sky-lg": "0 8px 24px rgba(79,195,247,.45)",
        red:      "0 4px 14px rgba(239,68,68,.35)",
        "red-lg": "0 8px 24px rgba(239,68,68,.4)",
      },
    },
  },
  plugins: [],
};
