"""Real-mode models (MODEL_MODE=real). Heavy libraries are imported lazily, so stub mode
never needs them. Train the weights with the notebooks in training/ and point the paths in
.env at the outputs. Every real model keeps the same interface as its stub.

Safety note: whatever these models return, the pipeline still applies the rules floor
(safety_rules.py), so a model can only make the system more cautious.
"""
from __future__ import annotations

import json
import logging
import urllib.request

from ... import config
from ..stub import StubExplainer, StubLanguageId, StubSituationClassifier, StubTriage

log = logging.getLogger(__name__)
URGENCY_LABELS = ["emergency", "clinic", "home"]


class RealLanguageId:
    """IndicLID (native and romanised). Falls back to the stub rules if IndicLID is missing."""

    def __init__(self) -> None:
        self._fallback = StubLanguageId()
        try:
            from ai4bharat.IndicLID import IndicLID  # type: ignore

            self._model = IndicLID(input_threshold=0.5, roman_lid_threshold=0.6)
        except Exception as exc:  # pragma: no cover - depends on optional install
            log.warning("IndicLID unavailable (%s); using stub language id", exc)
            self._model = None

    def detect(self, text: str) -> dict:
        if self._model is None:
            return self._fallback.detect(text)
        _, _, label, *_ = self._model.batch_predict([text], 1)[0]
        mapping = {"hin_Deva": ("hi", "devanagari"), "mar_Deva": ("mr", "devanagari"), "hin_Latn": ("hinglish", "latin"), "eng_Latn": ("en", "latin")}
        lang, script = mapping.get(label, (None, None))
        return {"lang": lang, "script": script} if lang else self._fallback.detect(text)


class RealTriage:
    """Fine-tuned IndicBERT v2 sequence classifier (emergency / clinic / home)."""

    def __init__(self) -> None:
        from transformers import AutoModelForSequenceClassification, AutoTokenizer  # type: ignore

        self.tok = AutoTokenizer.from_pretrained(config.TRIAGE_MODEL_PATH)
        self.model = AutoModelForSequenceClassification.from_pretrained(config.TRIAGE_MODEL_PATH).eval()
        self._rules = StubTriage()  # harmful-action myth matching stays rule-based until its head is trained

    def predict(self, text: str, lang: str, slots: dict) -> dict:
        import torch  # type: ignore

        with torch.no_grad():
            enc = self.tok(text, return_tensors="pt", truncation=True, max_length=128)
            probs = torch.softmax(self.model(**enc).logits[0], dim=-1).tolist()
        scores = dict(zip(URGENCY_LABELS, probs))
        rule_out = self._rules.predict(text, lang, slots)
        return {"urgency": max(scores, key=scores.get), "scores": scores, "harmful": rule_out["harmful"], "all_harmful": rule_out["all_harmful"]}


class RealSituationClassifier:
    """BGE-M3 dense embeddings: nearest situation prototype (recognition text + training queries)."""

    def __init__(self) -> None:
        from FlagEmbedding import BGEM3FlagModel  # type: ignore

        from ... import content

        self.model = BGEM3FlagModel(config.SITUATION_MODEL_NAME, use_fp16=False)
        self.labels: list[str] = []
        texts: list[str] = []
        for sid, rec in content.situations().items():
            for r in rec["recognition"]:
                for v in r.values():
                    if v:
                        self.labels.append(sid)
                        texts.append(v)
        texts += ["stroke, fracture, fever, poisoning or a seizure", "बुखार, जहर, लकवा, मिर्गी", "ताप, विषबाधा, अपघात"]
        self.labels += ["out_of_scope"] * 3
        self.protos = self.model.encode(texts)["dense_vecs"]

    def predict(self, text: str, lang: str) -> list[dict]:
        import numpy as np  # type: ignore

        q = self.model.encode([text])["dense_vecs"][0]
        sims = self.protos @ q
        best: dict[str, float] = {}
        for lab, s in zip(self.labels, sims):
            best[lab] = max(best.get(lab, -1.0), float(s))
        names = list(best)
        logits = np.array([best[n] for n in names]) * 20.0
        p = np.exp(logits - logits.max())
        p = p / p.sum()
        out = [{"situation": n, "p": float(v)} for n, v in zip(names, p)]
        return sorted(out, key=lambda d: -d["p"])


class RealStepVerifier:
    """mmBERT fine-tuned for entailment (IndicXNLI). Label 0 = entailment."""

    def __init__(self) -> None:
        from transformers import AutoModelForSequenceClassification, AutoTokenizer  # type: ignore

        self.tok = AutoTokenizer.from_pretrained(config.VERIFIER_MODEL_PATH)
        self.model = AutoModelForSequenceClassification.from_pretrained(config.VERIFIER_MODEL_PATH).eval()

    def entails(self, verified: str, candidate: str, lang: str) -> bool:
        import torch  # type: ignore

        with torch.no_grad():
            enc = self.tok(verified, candidate, return_tensors="pt", truncation=True)
            label = int(self.model(**enc).logits[0].argmax())
        return label == 0


class RealRephraser:
    """Gemma 3 4B through a local Ollama server. Uses only the current record as context."""

    PROMPT = (
        "Rewrite this first aid instruction in simpler {lang} words for a panicked bystander. "
        "Keep every number, every action and every warning. Do not add anything. "
        "Reply with the rewritten sentence only.\n\nInstruction: {step}"
    )
    LANG_NAMES = {"en": "English", "hi": "Hindi", "hinglish": "Hinglish (romanised Hindi)", "mr": "Marathi"}

    def rephrase(self, step: str, lang: str, record: dict) -> str | None:
        body = json.dumps({"model": config.GEMMA_MODEL, "prompt": self.PROMPT.format(lang=self.LANG_NAMES[lang], step=step), "stream": False}).encode()
        req = urllib.request.Request(f"{config.OLLAMA_URL}/api/generate", data=body, headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                return json.loads(resp.read())["response"].strip() or None
        except Exception as exc:  # pragma: no cover - needs a running Ollama
            log.warning("Rephraser unavailable: %s", exc)
            return None


class RealExplainer(StubExplainer):
    """Token attributions on the triage model with transformers-interpret.
    Rule-triggered alerts still name the rule's trigger words (Section 8.6)."""

    def __init__(self, triage: RealTriage) -> None:
        super().__init__()
        from transformers_interpret import SequenceClassificationExplainer  # type: ignore

        self.cls = SequenceClassificationExplainer(triage.model, triage.tok)

    def explain(self, text: str, lang: str, urgency: str, triggers=None) -> list[dict]:
        rule_words = super().explain(text, lang, urgency, triggers)
        if rule_words or urgency != "emergency":
            return rule_words
        attrs = self.cls(text, class_name="emergency")
        words: list[dict] = []
        for tok, w in sorted(attrs, key=lambda x: -x[1]):
            clean = tok.replace("▁", "").replace("##", "")
            if w < 0.2 or not clean.strip() or clean.startswith("["):
                continue
            idx = text.lower().find(clean.lower())
            if idx >= 0:
                end = idx
                while end < len(text) and not text[end].isspace():
                    end += 1
                start = idx
                while start > 0 and not text[start - 1].isspace():
                    start -= 1
                words.append({"word": text[start:end], "start": start, "end": end, "weight": round(float(w), 2)})
            if len(words) == 3:
                break
        return words


def build() -> dict:
    triage = RealTriage()
    return {
        "langid": RealLanguageId(),
        "triage": triage,
        "situation": RealSituationClassifier(),
        "verifier": RealStepVerifier(),
        "rephraser": RealRephraser() if config.REPHRASE_ENABLED else None,
        "explainer": RealExplainer(triage),
    }
