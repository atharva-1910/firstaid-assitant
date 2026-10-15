"""Builds the template-based training and development query sets (Section 10).

Gold labels come from the templates, never from a model (Section 10.3). The hand-written
test set (data/queries/test.jsonl) is written by each language owner and is never
produced by this script.

    python scripts/generate_queries.py            # 150 per class per language, 80/20 train/dev
    python scripts/generate_queries.py --per-class 60
"""
from __future__ import annotations

import argparse
import itertools
import json
import random
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "data" / "queries"

# Each template: (text, situation, subtype, urgency, slots). {p} = person, {t} = time.
PEOPLE = {
    "en": ["my father", "my mother", "my uncle", "an old man", "my colleague", "a woman", "my husband", "my neighbour"],
    "hinglish": ["papa", "mummy", "chacha", "dadaji", "bhaiya", "ek aadmi", "meri wife", "padosi"],
    "hi": ["पापा", "मम्मी", "चाचा", "दादाजी", "भैया", "एक आदमी", "मेरी पत्नी", "पड़ोसी"],
    "mr": ["बाबा", "आई", "काका", "आजोबा", "दादा", "एक माणूस", "माझी बायको", "शेजारी"],
}
TIMES = {
    "en": ["", " 10 minutes ago", " just now", " about 20 minutes ago"],
    "hinglish": ["", " 10 minute pehle", " abhi abhi", " 20 minute pehle"],
    "hi": ["", " 10 मिनट पहले", " अभी अभी", " 20 मिनट पहले"],
    "mr": ["", " 10 मिनिटांपूर्वी", " आत्ताच", " 20 मिनिटांपूर्वी"],
}
WRAPS = {
    "en": ["{x}", "{x}, please help", "help! {x}", "{x}. what do I do?", "{x} what should i do"],
    "hinglish": ["{x}", "{x}, kya karu", "jaldi batao {x}", "{x}. madad karo", "{x} ab kya karein"],
    "hi": ["{x}", "{x}, क्या करूं", "जल्दी बताइए {x}", "{x}। मदद करो", "{x} अब क्या करें"],
    "mr": ["{x}", "{x}, काय करू", "लवकर सांगा {x}", "{x}. मदत करा", "{x} आता काय करायचं"],
}

E, C, H = "emergency", "clinic", "home"
T = {
    "en": {
        "unresponsive": [
            ("{p} collapsed and is not breathing{t}", "path_a", E, {"breathing": "absent"}),
            ("{p} is unconscious and only gasping{t}", "path_a", E, {"responsive": "no", "breathing": "abnormal"}),
            ("{p} fainted and is not responding{t}", None, E, {"responsive": "no"}),
            ("{p} passed out but is breathing normally", "path_b", E, {"responsive": "no", "breathing": "normal"}),
            ("{p} won't wake up{t}", None, E, {"responsive": "no"}),
            ("found {p} lying on the floor, no breathing", "path_a", E, {"breathing": "absent"}),
        ],
        "heart_attack": [
            ("{p} has chest pain{t}", None, E, {"chest_pain": "yes"}),
            ("{p} says there is pressure in the chest and is sweating", None, E, {"chest_pain": "yes"}),
            ("I think {p} is having a heart attack", None, E, {}),
            ("{p} has tightness in the chest spreading to the left arm", None, E, {"chest_pain": "yes"}),
            ("{p} complains of heavy chest and breathlessness{t}", None, E, {"chest_pain": "yes"}),
        ],
        "choking": [
            ("{p} is choking on food and cannot speak", None, E, {"choking_signs": "weak_or_silent"}),
            ("{p} is choking, turning blue{t}", None, E, {"choking_signs": "weak_or_silent"}),
            ("food stuck in throat, {p} can't breathe", None, E, {"choking_signs": "weak_or_silent"}),
            ("{p} is choking but coughing hard", None, H, {"choking_signs": "coughing_strongly"}),
            ("a bone is stuck in the throat of {p}", None, None, {}),
        ],
        "bites": [
            ("a snake bit {p} on the leg{t}", "snake", E, {"bite_type": "snake"}),
            ("{p} was bitten by a cobra in the field", "snake", E, {"bite_type": "snake"}),
            ("a bee stung {p} on the hand", "insect_sting", H, {"bite_type": "insect_sting"}),
            ("{p} was stung by a wasp and the face is swelling", "insect_sting", E, {"bite_type": "insect_sting", "allergy_signs": "yes"}),
            ("a scorpion stung {p}{t}", "scorpion", C, {"bite_type": "scorpion"}),
            ("a stray dog bit {p}{t}", "dog", C, {"bite_type": "dog"}),
            ("a dog bit {p} and the bleeding won't stop", "dog", E, {"bite_type": "dog"}),
            ("a monkey bit {p}", "dog", C, {"bite_type": "other_mammal"}),
        ],
        "burns": [
            ("{p} burned the arm with boiling water{t}", "fire_heat", C, {"burn_cause": "hot_liquid_steam"}),
            ("{p} has a small burn from the iron", "fire_heat", H, {"burn_cause": "fire_heat", "burn_area": "small"}),
            ("{p} burned the face on the stove", "fire_heat", E, {"burn_cause": "fire_heat", "burn_area": "eyes_or_face"}),
            ("acid splashed in the eye of {p}", "chemical_acid", E, {"burn_cause": "chemical_acid", "burn_area": "eyes_or_face"}),
            ("{p} spilled toilet cleaner on the leg", "chemical_acid", C, {"burn_cause": "chemical_acid"}),
            ("{p} got an electric shock from a wire{t}", "electrical", E, {"burn_cause": "electrical"}),
            ("{p} touched a live wire and got burned", "electrical", E, {"burn_cause": "electrical"}),
        ],
        "out_of_scope": [
            ("{p} has a high fever", None, None, {}),
            ("I think {p} is having a stroke", None, None, {}),
            ("{p} broke a leg in an accident", None, None, {}),
            ("{p} swallowed poison{t}", None, None, {}),
            ("{p} is having a seizure", None, None, {}),
            ("my 5 year old child has a fever", None, E, {"age_group": "child"}),
        ],
    },
    "hinglish": {
        "unresponsive": [
            ("{p} gir gaye, saans nahi le rahe{t}", "path_a", E, {"breathing": "absent"}),
            ("{p} behosh ho gaye hain, jawab nahi de rahe", None, E, {"responsive": "no"}),
            ("{p} uth nahi rahe, haanf rahe hain", "path_a", E, {"responsive": "no", "breathing": "abnormal"}),
            ("{p} behosh hain par saans theek hai", "path_b", E, {"responsive": "no", "breathing": "normal"}),
            ("{p} ko hosh nahi aa raha{t}", None, E, {"responsive": "no"}),
        ],
        "heart_attack": [
            ("{p} ke seene mein dard ho raha hai{t}", None, E, {"chest_pain": "yes"}),
            ("{p} ko lagta hai heart attack aaya", None, E, {}),
            ("{p} ki chhati mein dabav hai aur paseena", None, E, {"chest_pain": "yes"}),
            ("{p} ke seene mein bhaaripan hai", None, E, {"chest_pain": "yes"}),
        ],
        "choking": [
            ("{p} ke gale mein khana atak gaya, bol nahi pa rahe", None, E, {"choking_signs": "weak_or_silent"}),
            ("{p} ke gale mein haddi phas gayi{t}", None, None, {}),
            ("{p} ke gale mein kuch atak gaya, awaaz nahi", None, E, {"choking_signs": "weak_or_silent"}),
            ("{p} zor se khaans rahe hain, khana atka", None, H, {"choking_signs": "coughing_strongly"}),
        ],
        "bites": [
            ("{p} ko saap ne kaat liya{t}", "snake", E, {"bite_type": "snake"}),
            ("khet mein {p} ko saanp ne pair pe kaata", "snake", E, {"bite_type": "snake"}),
            ("{p} ko madhumakkhi ne dank mara", "insect_sting", H, {"bite_type": "insect_sting"}),
            ("{p} ko bichhu ne kaat liya{t}", "scorpion", C, {"bite_type": "scorpion"}),
            ("{p} ko kutte ne kaat liya", "dog", C, {"bite_type": "dog"}),
            ("{p} ko kutte ne kaata, khoon ruk nahi raha", "dog", E, {"bite_type": "dog"}),
        ],
        "burns": [
            ("{p} garam paani se jal gaye{t}", "fire_heat", C, {"burn_cause": "hot_liquid_steam"}),
            ("{p} ka haath tawa se jal gaya", "fire_heat", E, {"burn_cause": "fire_heat", "burn_area": "sensitive_area"}),
            ("{p} ki aankh mein tezaab chala gaya", "chemical_acid", E, {"burn_cause": "chemical_acid", "burn_area": "eyes_or_face"}),
            ("{p} ko current laga{t}", "electrical", E, {"burn_cause": "electrical"}),
            ("{p} ko bijli ka jhatka laga", "electrical", E, {"burn_cause": "electrical"}),
        ],
        "out_of_scope": [
            ("{p} ko bahut bukhar hai", None, None, {}),
            ("{p} ko lakwa maar gaya lagta hai", None, None, {}),
            ("{p} ki haddi toot gayi accident mein", None, None, {}),
            ("{p} ne zeher kha liya", None, None, {}),
            ("{p} ko mirgi ka daura pada", None, None, {}),
        ],
    },
    "hi": {
        "unresponsive": [
            ("{p} गिर गए, सांस नहीं ले रहे{t}", "path_a", E, {"breathing": "absent"}),
            ("{p} बेहोश हो गए हैं, जवाब नहीं दे रहे", None, E, {"responsive": "no"}),
            ("{p} उठ नहीं रहे, बस हांफ रहे हैं", "path_a", E, {"responsive": "no", "breathing": "abnormal"}),
            ("{p} बेहोश हैं पर सांस ठीक है", "path_b", E, {"responsive": "no", "breathing": "normal"}),
        ],
        "heart_attack": [
            ("{p} के सीने में दर्द हो रहा है{t}", None, E, {"chest_pain": "yes"}),
            ("लगता है {p} को दिल का दौरा पड़ा है", None, E, {}),
            ("{p} की छाती में भारीपन और पसीना", None, E, {"chest_pain": "yes"}),
        ],
        "choking": [
            ("{p} के गले में खाना अटक गया, बोल नहीं पा रहे", None, E, {"choking_signs": "weak_or_silent"}),
            ("{p} के गले में हड्डी फंस गई{t}", None, None, {}),
            ("{p} जोर से खांस रहे हैं, खाना अटका है", None, H, {"choking_signs": "coughing_strongly"}),
        ],
        "bites": [
            ("{p} को सांप ने काट लिया{t}", "snake", E, {"bite_type": "snake"}),
            ("{p} को मधुमक्खी ने डंक मारा", "insect_sting", H, {"bite_type": "insect_sting"}),
            ("{p} को बिच्छू ने डंक मारा{t}", "scorpion", C, {"bite_type": "scorpion"}),
            ("{p} को कुत्ते ने काट लिया", "dog", C, {"bite_type": "dog"}),
        ],
        "burns": [
            ("{p} गरम पानी से जल गए{t}", "fire_heat", C, {"burn_cause": "hot_liquid_steam"}),
            ("{p} की आंख में तेजाब चला गया", "chemical_acid", E, {"burn_cause": "chemical_acid", "burn_area": "eyes_or_face"}),
            ("{p} को करंट लग गया{t}", "electrical", E, {"burn_cause": "electrical"}),
            ("{p} का चेहरा आग से जल गया", "fire_heat", E, {"burn_cause": "fire_heat", "burn_area": "eyes_or_face"}),
        ],
        "out_of_scope": [
            ("{p} को तेज बुखार है", None, None, {}),
            ("{p} को लकवा मार गया लगता है", None, None, {}),
            ("{p} ने जहर खा लिया", None, None, {}),
            ("{p} को मिर्गी का दौरा पड़ा", None, None, {}),
        ],
    },
    "mr": {
        "unresponsive": [
            ("{p} खाली पडले, श्वास घेत नाहीत{t}", "path_a", E, {"breathing": "absent"}),
            ("{p} बेशुद्ध आहेत, प्रतिसाद देत नाहीत", None, E, {"responsive": "no"}),
            ("{p} बेशुद्ध आहेत पण श्वास नीट आहे", "path_b", E, {"responsive": "no", "breathing": "normal"}),
            ("{p} उठत नाहीत, घरघर आवाज येतोय", "path_a", E, {"responsive": "no", "breathing": "abnormal"}),
        ],
        "heart_attack": [
            ("{p} यांच्या छातीत दुखत आहे{t}", None, E, {"chest_pain": "yes"}),
            ("{p} यांना हार्ट अटॅक आला असं वाटतंय", None, E, {}),
            ("{p} यांच्या छातीत दाब आणि घाम", None, E, {"chest_pain": "yes"}),
        ],
        "choking": [
            ("{p} यांच्या घशात घास अडकला, बोलता येत नाही", None, E, {"choking_signs": "weak_or_silent"}),
            ("{p} यांच्या घशात हाड अडकलं{t}", None, None, {}),
            ("{p} जोरात खोकत आहेत, घास अडकला", None, H, {"choking_signs": "coughing_strongly"}),
        ],
        "bites": [
            ("{p} यांना साप चावला{t}", "snake", E, {"bite_type": "snake"}),
            ("{p} यांना मधमाशीने डंख मारला", "insect_sting", H, {"bite_type": "insect_sting"}),
            ("{p} यांना विंचू चावला{t}", "scorpion", C, {"bite_type": "scorpion"}),
            ("{p} यांना कुत्रा चावला", "dog", C, {"bite_type": "dog"}),
        ],
        "burns": [
            ("{p} गरम पाण्याने भाजले{t}", "fire_heat", C, {"burn_cause": "hot_liquid_steam"}),
            ("{p} यांच्या डोळ्यात ॲसिड गेलं", "chemical_acid", E, {"burn_cause": "chemical_acid", "burn_area": "eyes_or_face"}),
            ("{p} यांना विजेचा धक्का बसला{t}", "electrical", E, {"burn_cause": "electrical"}),
            ("{p} यांचा चेहरा आगीत भाजला", "fire_heat", E, {"burn_cause": "fire_heat", "burn_area": "eyes_or_face"}),
        ],
        "out_of_scope": [
            ("{p} यांना खूप ताप आहे", None, None, {}),
            ("{p} यांना पक्षाघात झाला असं वाटतं", None, None, {}),
            ("{p} यांनी विष घेतलं", None, None, {}),
            ("{p} यांना फिट आली", None, None, {}),
        ],
    },
}
PREFIX = {"en": "en", "hinglish": "hg", "hi": "hi", "mr": "mr"}


def generate(per_class: int, seed: int = 13, dev_share: float = 0.2) -> tuple[list[dict], list[dict]]:
    rng = random.Random(seed)
    train, dev = [], []
    for lang, classes in T.items():
        for situation, templates in classes.items():
            combos = list(itertools.product(templates, PEOPLE[lang], TIMES[lang], WRAPS[lang]))
            rng.shuffle(combos)
            seen: set[str] = set()
            rows = []
            for (tmpl, sub, urg, slots), person, time, wrap in combos:
                text = wrap.format(x=tmpl.format(p=person, t=time)).strip()
                if text in seen:
                    continue
                seen.add(text)
                s = dict(slots)
                s.setdefault("age_group", "adult")
                if time.strip() and any(c.isdigit() for c in time):
                    s["time_since"] = time.strip().replace("about ", "").split(" ago")[0].replace(" pehle", "").replace(" पहले", "").replace("पूर्वी", "")
                rows.append({
                    "id": f"{PREFIX[lang]}-{situation[:5]}-{len(rows) + 1:04d}",
                    "lang": lang,
                    "text": text,
                    "situation": situation,
                    "subtype": sub,
                    "urgency": urg,
                    "slots": s,
                    "split": "",
                    "written_by": "template",
                })
                if len(rows) >= per_class:
                    break
            n_dev = max(1, int(len(rows) * dev_share))
            for i, r in enumerate(rows):
                r["split"] = "dev" if i < n_dev else "train"
                (dev if i < n_dev else train).append(r)
    return train, dev


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-class", type=int, default=150)
    ap.add_argument("--seed", type=int, default=13)
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    train, dev = generate(args.per_class, args.seed)
    for name, rows in (("train", train), ("dev", dev)):
        with open(OUT / f"{name}.jsonl", "w", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"train={len(train)} dev={len(dev)} -> {OUT}")


if __name__ == "__main__":
    main()
