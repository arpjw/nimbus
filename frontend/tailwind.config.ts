import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        bg:         "#080808",
        surface:    "#111111",
        "surface-2":"#1A1A1A",
        border:     "#222222",
        "border-2": "#333333",
        text:       "#F0F0F0",
        muted:      "#888888",
        faint:      "#444444",
        accent:     "#7C3AED",
        "accent-light": "#A78BFA",
        orange:     "#FF6B35",
      },
      fontFamily: {
        sans:  ["var(--font-jakarta)", "system-ui", "sans-serif"],
        mono:  ["var(--font-jetbrains)", "monospace"],
      },
      animation: {
        "fade-up": "fadeUp 0.6s ease forwards",
      },
    },
  },
  plugins: [],
};
export default config;
