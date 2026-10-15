import { readdirSync, readFileSync, statSync } from "node:fs";
import { join } from "node:path";

import tailwind from "../../tailwind.config.js";
import { colors, contrastPairs } from "../theme/tokens";

function luminance(hex: string): number {
  const [r, g, b] = [1, 3, 5].map((i) => parseInt(hex.slice(i, i + 2), 16) / 255).map((c) => (c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4));
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}
function contrast(a: string, b: string): number {
  const [hi, lo] = [luminance(a), luminance(b)].sort((x, y) => y - x);
  return (hi + 0.05) / (lo + 0.05);
}

describe("design system (Section 14)", () => {
  it.each(contrastPairs)("%s on %s meets WCAG AA 4.5:1", (fg, bg) => {
    expect(contrast(colors[fg], colors[bg])).toBeGreaterThanOrEqual(4.5);
  });

  it("tailwind colours match the tokens", () => {
    const tw = (tailwind as { theme: { extend: { colors: Record<string, string> } } }).theme.extend.colors;
    for (const [k, v] of Object.entries(colors)) expect(tw[k]?.toUpperCase()).toBe(v.toUpperCase());
  });

  it("red (emergency) is used only by the Call 112 button and the emergency banner", () => {
    const allowed = new Set(["Call112Button.tsx", "EmergencyBanner.tsx"]);
    const root = join(__dirname, "..");
    const offenders: string[] = [];
    const walk = (dir: string) => {
      for (const f of readdirSync(dir)) {
        const p = join(dir, f);
        if (statSync(p).isDirectory()) {
          if (f !== "__tests__") walk(p);
        } else if (/\.(tsx?|css)$/.test(f) && !allowed.has(f) && f !== "tokens.ts") {
          if (/(bg|text|border|ring)-emergency/.test(readFileSync(p, "utf8"))) offenders.push(p);
        }
      }
    };
    walk(root);
    expect(offenders).toEqual([]);
  });
});
