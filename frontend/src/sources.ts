// The five guidelines (Section 4.1). Shown on the About screen and in the source chips.
export const SOURCES: Record<string, { short: string; title: string; publisher: string; year: string; url: string }> = {
  G1: {
    short: "IFRC 2025",
    title: "International First Aid, Resuscitation and Education Guidelines 2025",
    publisher: "IFRC",
    year: "2026",
    url: "https://www.ifrc.org/media/78476",
  },
  G2: {
    short: "AHA/Red Cross 2024",
    title: "2024 American Heart Association and American Red Cross Guidelines for First Aid",
    publisher: "AHA and American Red Cross",
    year: "2024",
    url: "https://www.ahajournals.org/doi/10.1161/CIR.0000000000001281",
  },
  G3: {
    short: "AHA BLS 2025",
    title: "2025 AHA Guidelines for CPR and ECC, Part 7: Adult Basic Life Support",
    publisher: "AHA",
    year: "2025",
    url: "https://cpr.heart.org/en/resuscitation-science/cpr-and-ecc-guidelines/adult-basic-life-support",
  },
  G4: {
    short: "ILCOR 2025",
    title: "2025 International Consensus on First Aid Science With Treatment Recommendations",
    publisher: "ILCOR",
    year: "2025",
    url: "https://www.ilcor.org/uploads/FA-2025-COSTR-Full-Chapter.pdf",
  },
  G5: {
    short: "NAPSE (MoHFW)",
    title: "National Action Plan for Prevention and Control of Snakebite Envenoming",
    publisher: "Ministry of Health and Family Welfare, Government of India",
    year: "2024",
    url: "https://ncdc.mohfw.gov.in/wp-content/uploads/2024/07/NATIONAL-ACTION-PLAN-FOR-PREVENTION-AND-CONTROL-OF-SNAKEBITE-ENVENOMING-NAPSE.pdf",
  },
};

export const TEAM = [
  { name: "Taneesha Badhe", prn: "1032232190", role: "English · F1 extraction · Unresponsive, Heart attack · BGE-M3" },
  { name: "Atharva Hemade", prn: "1032232249", role: "Hindi · F2 clarifying question and memory · Choking · Gemma 3" },
  { name: "Siddhi Karhekar", prn: "1032232132", role: "Marathi · F3 negation · Bites · mmBERT" },
  { name: "Soham Ghodake", prn: "1032232337", role: "Hinglish · F4 explainable alert · Burns · IndicBERT v2" },
];
