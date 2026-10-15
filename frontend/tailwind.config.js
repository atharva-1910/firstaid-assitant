/** @type {import('tailwindcss').Config} */
// Tokens are copied from src/theme/tokens.ts (keep in sync; a test checks they match).
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        bg: "#F5F8FA",
        surface: "#FFFFFF",
        primary: "#2F6F8F",
        "primary-soft": "#E6F0F5",
        text: "#1F2933",
        "text-muted": "#52606D",
        success: "#2F855A",
        "caution-text": "#8A5A00",
        "caution-bg": "#FFF8E6",
        emergency: "#C53030",
        "emergency-soft": "#FDECEC",
        border: "#D9E2EC",
      },
      fontSize: {
        step: ["24px", { lineHeight: "1.5", fontWeight: "600" }],
        question: ["22px", { lineHeight: "1.5", fontWeight: "600" }],
        body: ["18px", { lineHeight: "1.5" }],
        note: ["14px", { lineHeight: "1.5" }],
      },
      fontFamily: {
        sans: ['"Noto Sans"', '"Noto Sans Devanagari"', "system-ui", "sans-serif"],
        deva: ['"Noto Sans Devanagari"', '"Noto Sans"', "system-ui", "sans-serif"],
      },
      maxWidth: { column: "480px" },
      borderRadius: { card: "12px" },
    },
  },
  plugins: [],
};
