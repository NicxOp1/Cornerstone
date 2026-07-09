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
        "card-2": "rgb(var(--card-2) / <alpha-value>)",
        "cornerstone-navy": "#1E1B4B",
        "cornerstone-yellow": "#F5E000",
        good: "rgb(var(--good) / <alpha-value>)",
        "good-soft": "rgb(var(--good-soft) / <alpha-value>)",
        ground: "rgb(var(--ground) / <alpha-value>)",
        "ground-2": "rgb(var(--ground-2) / <alpha-value>)",
        heat: "rgb(var(--heat) / <alpha-value>)",
        ink: "rgb(var(--ink) / <alpha-value>)",
        "ink-soft": "rgb(var(--ink-soft) / <alpha-value>)",
        line: "rgb(var(--line) / <alpha-value>)",
        "line-strong": "rgb(var(--line-strong) / <alpha-value>)",
        muted: "rgb(var(--muted) / <alpha-value>)",
        navy: "rgb(var(--navy) / <alpha-value>)",
        "navy-2": "rgb(var(--navy-2) / <alpha-value>)",
        neg: "rgb(var(--neg) / <alpha-value>)",
        neu: "rgb(var(--neu) / <alpha-value>)",
        pos: "rgb(var(--pos) / <alpha-value>)",
        unk: "rgb(var(--unk) / <alpha-value>)"
      },
      boxShadow: {
        panel:
          "0 30px 90px rgba(var(--shadow), 0.38), inset 0 1px 0 rgba(255, 255, 255, 0.04)"
      },
      fontFamily: {
        display: ['"Avenir Next Condensed"', '"Franklin Gothic Demi"', '"Arial Narrow"', "sans-serif"],
        sans: ['"Avenir Next"', '"Segoe UI"', "system-ui", "sans-serif"]
      }
    }
  },
  plugins: []
};

export default config;
