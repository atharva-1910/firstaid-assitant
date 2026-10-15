import en from "../i18n/en.json";
import hi from "../i18n/hi.json";
import hinglish from "../i18n/hinglish.json";
import mr from "../i18n/mr.json";

// Core strings from Section 15.1 must match the specification exactly.
const CORE: Record<string, Record<string, string>> = {
  call_112: { en: "Call 112", hi: "112 पर कॉल करें", hinglish: "112 par call karein", mr: "112 वर कॉल करा" },
  what_happened: { en: "What happened?", hi: "क्या हुआ?", hinglish: "Kya hua?", mr: "काय झालं?" },
  own_words: { en: "Tell us in your own words", hi: "अपने शब्दों में बताइए", hinglish: "Apne shabdon mein batayein", mr: "तुमच्या शब्दांत सांगा" },
  next: { en: "Done, next", hi: "हो गया, आगे", hinglish: "Ho gaya, aage", mr: "झालं, पुढे" },
  back: { en: "Back", hi: "पीछे", hinglish: "Peeche", mr: "मागे" },
  yes: { en: "Yes", hi: "हाँ", hinglish: "Haan", mr: "हो" },
  no: { en: "No", hi: "नहीं", hinglish: "Nahi", mr: "नाही" },
  not_sure: { en: "Not sure", hi: "पता नहीं", hinglish: "Pata nahi", mr: "माहीत नाही" },
  do_not: { en: "Please do not do this", hi: "कृपया ऐसा न करें", hinglish: "Kripya aisa na karein", mr: "कृपया हे करू नका" },
  reassure: { en: "Help is on the way. You are doing well.", hi: "मदद आ रही है। आप अच्छा कर रहे हैं।", hinglish: "Madad aa rahi hai. Aap achha kar rahe hain.", mr: "मदत येत आहे. तुम्ही छान करत आहात." },
  handover: { en: "Read this to the ambulance team", hi: "यह एम्बुलेंस टीम को पढ़कर सुनाएँ", hinglish: "Yeh ambulance team ko padh kar sunayein", mr: "हे रुग्णवाहिका टीमला वाचून दाखवा" },
  breathing_q: { en: "Is the person breathing normally?", hi: "क्या व्यक्ति सामान्य रूप से साँस ले रहा है?", hinglish: "Kya vyakti normal saans le raha hai?", mr: "ती व्यक्ती नीट श्वास घेत आहे का?" },
};
const FILES: Record<string, Record<string, string>> = { en, hi, hinglish, mr };

describe("i18n", () => {
  it("every language has every key", () => {
    const keys = Object.keys(en).sort();
    for (const [lang, dict] of Object.entries(FILES)) expect(Object.keys(dict).sort(), lang).toEqual(keys);
  });
  it("no empty strings", () => {
    for (const dict of Object.values(FILES)) for (const v of Object.values(dict)) expect(v.trim()).not.toBe("");
  });
  it.each(Object.keys(CORE))("core string %s matches Section 15.1", (key) => {
    for (const lang of Object.keys(FILES)) expect(FILES[lang][key]).toBe(CORE[key][lang]);
  });
});
