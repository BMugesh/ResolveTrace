import type { Config } from "tailwindcss";

export default {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "var(--background)",
        foreground: "var(--foreground)",
        spotify: {
          green: "#1DB954",
          dark: "#121212",
          card: "#181818",
          hover: "#282828",
          subtext: "#b3b3b3"
        }
      },
    },
  },
  plugins: [],
} satisfies Config;
