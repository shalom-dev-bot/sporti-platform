/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./templates/**/*.html",
    "./apps/**/templates/**/*.html",
    "./apps/**/forms.py",
    "./static/js/**/*.js",
  ],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        navy: {
          950: "#0B0F19",
          900: "#0D1321",
          850: "#121826",
          800: "#182236",
        },
        accent: {
          400: "#5B8DEF",
          500: "#3B82F6",
          600: "#2D6CDF",
        },
        surface: {
          light: "#F7F9FC",
          "light-elevated": "#FFFFFF",
        },
      },
      fontFamily: {
        display: ["Rajdhani", "sans-serif"],
        body: ["Inter", "sans-serif"],
        mono: ["JetBrains Mono", "monospace"],
      },
      boxShadow: {
        glow: "0 0 20px rgba(45, 108, 223, 0.35)",
        "glow-sm": "0 0 10px rgba(45, 108, 223, 0.25)",
      },
      keyframes: {
        "pulse-ring": {
          "0%": { boxShadow: "0 0 0 0 rgba(45, 108, 223, 0.5)" },
          "70%": { boxShadow: "0 0 0 8px rgba(45, 108, 223, 0)" },
          "100%": { boxShadow: "0 0 0 0 rgba(45, 108, 223, 0)" },
        },
        "fade-in-up": {
          "0%": { opacity: "0", transform: "translateY(8px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
      },
      animation: {
        "pulse-ring": "pulse-ring 2s cubic-bezier(0.4, 0, 0.6, 1) infinite",
        "fade-in-up": "fade-in-up 0.3s ease-out",
      },
    },
  },
  plugins: [],
};
