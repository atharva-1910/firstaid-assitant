// Colour and size tokens from Section 14 of the specification. Single source of truth:
// tailwind.config.js imports these, and the contrast test checks them.
export const colors = {
  bg: "#F5F8FA",
  surface: "#FFFFFF",
  primary: "#2F6F8F",
  "primary-soft": "#E6F0F5",
  text: "#1F2933",
  "text-muted": "#52606D",
  success: "#2F855A",
  "caution-text": "#8A5A00",
  "caution-bg": "#FFF8E6",
  emergency: "#C53030", // "Call 112" button and emergency banner only
  "emergency-soft": "#FDECEC",
  border: "#D9E2EC",
} as const;

export const fontSize = {
  step: ["24px", { lineHeight: "1.5", fontWeight: "600" }],
  question: ["22px", { lineHeight: "1.5", fontWeight: "600" }],
  body: ["18px", { lineHeight: "1.5", fontWeight: "400" }],
  note: ["14px", { lineHeight: "1.5", fontWeight: "400" }],
} as const;

// Text / background pairs that must meet WCAG 2.1 AA (4.5:1).
export const contrastPairs: Array<[keyof typeof colors, keyof typeof colors]> = [
  ["text", "bg"],
  ["text", "surface"],
  ["text-muted", "bg"],
  ["text-muted", "surface"],
  ["surface", "primary"],
  ["primary", "surface"],
  ["primary", "primary-soft"],
  ["text", "primary-soft"],
  ["caution-text", "caution-bg"],
  ["surface", "emergency"],
  ["emergency", "emergency-soft"],
  ["text", "emergency-soft"],
  ["success", "surface"],
];

export const CPR_BPM = 110;
