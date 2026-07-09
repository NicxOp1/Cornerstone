import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "media",
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        "cornerstone-navy": "#1E1B4B",
        "cornerstone-yellow": "#F5E000"
      }
    }
  },
  plugins: []
};

export default config;
