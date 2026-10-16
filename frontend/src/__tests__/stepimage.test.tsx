import { fireEvent, render, screen } from "@testing-library/react";

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

describe("step animation", () => {
  const anim = {
    src: "/steps/anim/ch_s4.svg", alt: "Moving picture: back blows.", title: "Back blows",
    author: "Multilingual First Aid Assistant team", license: "CC0 1.0",
    license_url: "https://creativecommons.org/publicdomain/zero/1.0/",
    source_url: "https://github.com/atharva-1910/firstaid-assitant/tree/main/docs/illustrations", verified: false,
  };
  it("shows the movement first and can switch to the still picture", () => {
    render(<StepCard step={{ ...step, animation: anim }} />);
    expect(screen.getByRole("img").getAttribute("src")).toBe("/steps/anim/ch_s4.svg");
    expect(screen.getByText(/Animation:/)).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Show still picture" }));
    expect(screen.getByRole("img").getAttribute("src")).toBe("/steps/unr_a3.webp");
    fireEvent.click(screen.getByRole("button", { name: "Show the movement" }));
    expect(screen.getByRole("img").getAttribute("src")).toBe("/steps/anim/ch_s4.svg");
  });
  it("shows the still picture first when the phone asks for reduced motion", () => {
    const mm = window.matchMedia;
    window.matchMedia = ((q: string) => ({ matches: q.includes("reduce"), media: q, addEventListener() {}, removeEventListener() {} })) as unknown as typeof window.matchMedia;
    render(<StepCard step={{ ...step, animation: anim }} />);
    expect(screen.getByRole("img").getAttribute("src")).toBe("/steps/unr_a3.webp");
    window.matchMedia = mm;
  });
});
