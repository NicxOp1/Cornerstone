import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "media",
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        accent: "rgb(var(--accent) / <alpha-value>)",
        "accent-ink": "rgb(var(--accent-ink) / <alpha-value>)",
        bad: "rgb(var(--bad) / <alpha-value>)",
        "bad-soft": "rgb(var(--bad-soft) / <alpha-value>)",
        card: "rgb(var(--card) / <alpha-value>)",
        "cornerstone-navy": "#1E1B4B",
        "cornerstone-yellow": "#F5E000",
        good: "rgb(var(--good) / <alpha-value>)",
        "good-soft": "rgb(var(--good-soft) / <alpha-value>)",
        ground: "rgb(var(--ground) / <alpha-value>)",
        heat: "rgb(var(--heat) / <alpha-value>)",
        ink: "rgb(var(--ink) / <alpha-value>)",
        "ink-soft": "rgb(var(--ink-soft) / <alpha-value>)",
        line: "rgb(var(--line) / <alpha-value>)",
        muted: "rgb(var(--muted) / <alpha-value>)",
        navy: "rgb(var(--navy) / <alpha-value>)",
        "navy-2": "rgb(var(--navy-2) / <alpha-value>)",
        neg: "rgb(var(--neg) / <alpha-value>)",
        neu: "rgb(var(--neu) / <alpha-value>)",
        pos: "rgb(var(--pos) / <alpha-value>)",
        unk: "rgb(var(--unk) / <alpha-value>)"
      },
      boxShadow: {
        panel: "0 24px 80px rgba(var(--shadow), 0.14)"
      },
      fontFamily: {
        display: ['"Iowan Old Style"', "Palatino Linotype", "Georgia", "serif"],
        sans: ["system-ui", "sans-serif"]
      }
    }
  },
  plugins: []
};

export default config;
