/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#101820",
        panel: "#17212b",
        panelSoft: "#1f2b35",
        line: "#31414f",
        accent: "#7dd3c7",
        honey: "#f6bd60",
        coral: "#f28482",
        mist: "#d8f3dc",
      },
    },
  },
  plugins: [],
};
