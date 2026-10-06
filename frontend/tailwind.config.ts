import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Inter", "-apple-system", "BlinkMacSystemFont", "Segoe UI", "Roboto", "Arial", "sans-serif"],
      },
    },
  },
  plugins: [require("daisyui")],
  daisyui: {
    logs: false,
    darkTheme: "eqdark",
    themes: [
      {
        eqlight: {
          primary: "#4A8FD6",
          "primary-content": "#ffffff",
          secondary: "#4A8FD6",
          "secondary-content": "#ffffff",
          accent: "#4A8FD6",
          "accent-content": "#ffffff",
          neutral: "#1A1A1F",
          "neutral-content": "#ffffff",
          "base-100": "#FFFFFF",
          "base-200": "#F9FAFB",
          "base-300": "#E5E7EB",
          "base-content": "#1A1A1F",
          info: "#4A8FD6",
          success: "#4A8FD6",
          warning: "#4A8FD6",
          error: "#1A1A1F",
          "--rounded-box": "14px",
          "--rounded-btn": "12px",
          "--rounded-badge": "999px",
          "--animation-btn": "0.15s",
          "--btn-focus-scale": "1",
          "--border-btn": "1px",
        },
        eqdark: {
          primary: "#4A8FD6",
          "primary-content": "#ffffff",
          secondary: "#4A8FD6",
          "secondary-content": "#ffffff",
          accent: "#4A8FD6",
          "accent-content": "#ffffff",
          neutral: "#E5E7EB",
          "neutral-content": "#0B0B0D",
          "base-100": "#0B0B0D",
          "base-200": "#141416",
          "base-300": "#26272B",
          "base-content": "#F3F4F6",
          info: "#4A8FD6",
          success: "#4A8FD6",
          warning: "#4A8FD6",
          error: "#E5E7EB",
          "--rounded-box": "14px",
          "--rounded-btn": "12px",
          "--rounded-badge": "999px",
          "--animation-btn": "0.15s",
          "--btn-focus-scale": "1",
          "--border-btn": "1px",
        },
      },
    ],
  },
};

export default config;
