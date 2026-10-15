import i18n from "i18next";
import { initReactI18next } from "react-i18next";

import en from "./en.json";
import hi from "./hi.json";
import hinglish from "./hinglish.json";
import mr from "./mr.json";
import type { Lang } from "../api/client";

export const LANGUAGES: { code: Lang; label: string; script: "latin" | "devanagari" }[] = [
  { code: "en", label: "English", script: "latin" },
  { code: "hi", label: "हिंदी", script: "devanagari" },
  { code: "hinglish", label: "Hinglish", script: "latin" },
  { code: "mr", label: "मराठी", script: "devanagari" },
];

export const resources = {
  en: { translation: en },
  hi: { translation: hi },
  hinglish: { translation: hinglish },
  mr: { translation: mr },
};

i18n.use(initReactI18next).init({
  resources,
  lng: "en",
  fallbackLng: "en",
  interpolation: { escapeValue: false },
  returnEmptyString: false,
});

export function scriptOf(lang: Lang): "latin" | "devanagari" {
  return LANGUAGES.find((l) => l.code === lang)?.script ?? "latin";
}

export default i18n;
