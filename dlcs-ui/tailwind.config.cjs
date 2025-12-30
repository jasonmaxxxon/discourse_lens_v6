/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{ts,tsx,jsx,js}"],
  theme: {
    extend: {
      colors: {
        background: "#0b1021",
        card: "#0f172a",
        accent: "#22d3ee",
        subtle: "#94a3b8",
        primary: "#f425c0",
        "background-light": "#f8f5f8",
        "background-dark": "#22101e",
        midnight: "#0B0C15",
        "neon-cyan": "#00f3ff",
        "neon-yellow": "#ccff00",
        "neon-purple": "#bc13fe",
      },
      boxShadow: {
        glow: "0 10px 50px rgba(34, 211, 238, 0.25)",
        hard: "4px 4px 0px 0px rgba(148,163,184,0.6)",
      },
      fontFamily: {
        display: ["Space Grotesk", "sans-serif"],
        serif: ["Playfair Display", "serif"],
      },
    },
  },
  plugins: [],
};
