import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        bg:             "#F7F4EF",
        surface:        "#EDE8DF",
        "surface-raised": "#E4DDD1",
        border:         "#D5CCC0",
        "border-dark":  "#B8ADA0",
        text:           "#18140E",
        muted:          "#7A6B5E",
        faint:          "#A89888",
        red:            "#8E2D2D",
        "red-light":    "#C4504A",
        brown:          "#4A3728",
      },
      fontFamily: {
        sans:    ["var(--font-inter)", "system-ui", "sans-serif"],
        display: ["var(--font-cormorant)", "Georgia", "serif"],
        mono:    ["var(--font-jetbrains)", "monospace"],
      },
    },
  },
  plugins: [],
};
export default config;
