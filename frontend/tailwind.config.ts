import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        display: ["Space Grotesk", "IBM Plex Sans", "sans-serif"],
        body: ["IBM Plex Sans", "Segoe UI", "sans-serif"],
      },
      colors: {
        canvas: "#f5f1e8",
        ink: "#1c211b",
        ember: "#f06a44",
        pine: "#2e5d50",
        sea: "#2d7891",
        sand: "#ddc49d",
      },
      boxShadow: {
        panel: "0 18px 48px rgba(20, 26, 24, 0.12)",
      },
    },
  },
  plugins: [],
} satisfies Config;
