import { render, screen } from "@testing-library/react";

import type { Step } from "../api/client";
import { StepCard } from "../components/StepCard";
import "../i18n";

const step: Step = {
  id: "unr_a3", order: 1, text: "Put the heel of one hand in the centre of the chest.", translation_pending: false, rephrased: false,
  source: { doc: "G1", page: 158 }, also_in: [], agreement: "unchecked", evidence: "unchecked", verified: false, cpr_rhythm: false,
  link: null, do_not: [],
  image: {
    src: "/steps/unr_a3.webp", alt: "Heel of one hand on the centre of the chest.", title: "CPR Adult Chest Compression",
    author: "BruceBlaus", license: "CC BY-SA 4.0", license_url: "https://creativecommons.org/licenses/by-sa/4.0/",
    source_url: "https://commons.wikimedia.org/wiki/File:CPR_Adult_Chest_Compression.png", verified: false,
  },
};

describe("step image", () => {
  it("shows the picture with alt text and a licence credit", () => {
    render(<StepCard step={step} />);
    expect(screen.getByRole("img").getAttribute("alt")).toBe("Heel of one hand on the centre of the chest.");
    expect(screen.getByRole("link", { name: "BruceBlaus" }).getAttribute("href")).toContain("commons.wikimedia.org");
    expect(screen.getByRole("link", { name: "CC BY-SA 4.0" })).toBeTruthy();
  });
  it("shows no figure when a step has no image", () => {
    render(<StepCard step={{ ...step, image: null }} />);
    expect(screen.queryByRole("img")).toBeNull();
  });
});
