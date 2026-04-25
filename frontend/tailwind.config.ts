import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        bg: "#080810",
        surface: "#0E0E1A",
        "surface-raised": "#141424",
        border: "#1E1E32",
        "border-bright": "#2E2E48",
        text: "#E8E8F4",
        muted: "#6A6A8E",
        accent: "#3EFFA8",
        "accent-dim": "#1A7A50",
        danger: "#FF4E6A",
        warning: "#FFB340",
        info: "#4EA8FF",
      },
      fontFamily: {
        sans: ["var(--font-syne)", "system-ui", "sans-serif"],
        body: ["var(--font-dm-sans)", "system-ui", "sans-serif"],
        mono: ["var(--font-jetbrains)", "monospace"],
      },
      animation: {
        "fade-in": "fadeIn 0.4s ease forwards",
        "slide-up": "slideUp 0.4s ease forwards",
        "pulse-accent": "pulseAccent 2s ease-in-out infinite",
        "scan": "scan 3s linear infinite",
      },
      keyframes: {
        fadeIn: { from: { opacity: "0" }, to: { opacity: "1" } },
        slideUp: { from: { opacity: "0", transform: "translateY(12px)" }, to: { opacity: "1", transform: "translateY(0)" } },
        pulseAccent: { "0%,100%": { opacity: "1" }, "50%": { opacity: "0.4" } },
        scan: { from: { transform: "translateY(-100%)" }, to: { transform: "translateY(100vh)" } },
      },
    },
  },
  plugins: [],
};

export default config;
