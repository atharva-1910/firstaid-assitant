# Switching to real models (MODEL_MODE=real)

Stub mode needs nothing extra. Real mode swaps each stand-in for the trained model behind the same interface (Section 12). The safety rules floor still applies, so a model can only raise urgency.

| Interface | Real model | Produced by | Default location |
|---|---|---|---|
| `LanguageId` | IndicLID (AI4Bharat) | install from AI4Bharat | falls back to the stub if it is missing |
| `Triage` | IndicBERT v2, fine-tuned | `training/04_triage_indicbert.ipynb` | `training/out/indicbert_triage` |
| `SituationClassifier` | BGE-M3 | downloaded from the Hugging Face Hub | `BAAI/bge-m3` |
| `StepVerifier` | mmBERT, fine-tuned on XNLI and IndicXNLI | `training/03_verifier_mmbert.ipynb` | `training/out/mmbert_verifier` |
| `Rephraser` (optional) | Gemma 3 4B via Ollama | `ollama pull gemma3:4b` | `OLLAMA_URL` |
| `Explainer` | transformers-interpret on the triage model | — | — |

## Steps

1. Run the notebooks in order on Colab with a GPU: first 03, then 04, then 01, then 02. Notebook 02 needs the verifier from 03. Copy `training/out/` back into the repo; it is git-ignored.
2. Install the runtime packages:
   ```bash
   cd backend
   pip install -r requirements-real.txt
   ```
3. IndicLID and IndicXlit: follow the AI4Bharat install instructions for IndicLID (Bhasha-Abhijnaanam) and `ai4bharat-transliteration`.
4. Optional rephrasing: install Ollama, run `ollama pull gemma3:4b`, and set `REPHRASE_ENABLED=true`.
5. Set `MODEL_MODE=real` in `.env` and start the backend. `GET /api/health` lists the models in use.
6. Run `python -m pytest -q` again. The safety suite must still pass at 100%.

The model ids in the notebooks (`ai4bharat/IndicBERTv2-MLM-only`, `jhu-clsp/mmBERT-base`, `BAAI/bge-m3`, `google/gemma-3-4b-it`, `Divyanshu/indicxnli`) were current when this was written. Check them on the Hub before training.
