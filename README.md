# Cultural Appropriateness Checker 🚧 (Work in Progress)
### Prompt-strategy evaluation for detecting cultural risk in global ad copy — on a small local LLM

> **Module 1 of a 4-module Cultural Intelligence Platform** (M.Sc. AI in Business, SRH Berlin).
> Can a cheap, locally-run 3B model flag culturally risky ad copy at the draft stage — and how much does prompt design drive that performance?

**TL;DR:** Three prompt strategies (zero-shot / persona / few-shot + step-by-step) were compared on 84 real-world ad samples across 8 cultures. The first run scored ~0% — not because the model couldn't reason, but because it couldn't produce valid JSON. After forcing structured output, few-shot (C) won on topic, intent, and label reliability; persona (B) kept risk classes most balanced. **Accuracy alone hid all of this — macro F1 told the real story.**

---

## Results

All versions at 0% JSON parse failure (fair comparison). Best value per row in **bold**.

| Metric | A (zero-shot) | B (persona) | C (few-shot) |
|---|---|---|---|
| Risk — accuracy | **0.595** | 0.571 | **0.595** |
| Risk — macro F1 | 0.336 | **0.452** | 0.392 |
| Topic — accuracy | 0.417 | 0.405 | **0.500** |
| Topic — macro F1 | 0.409 | 0.408 | **0.511** |
| Intent — accuracy | **0.631** | 0.571 | 0.595 |
| Intent — macro F1 | 0.353 | 0.380 | **0.409** |
| Label errors (bad_label, lower = better) | 8 | 9 | **2** |

**Reading it per task:**
- **Risk** — B wins on macro F1 (0.452). A and C push almost everything to *Taboo* and barely catch safe ads (Expected recall 0.00 / 0.07); B recovers many Expected (recall 0.39) at the cost of missing some real Taboo.
- **Topic** — C is clearly best (macro F1 0.511). Few-shot examples helped it spread across all six topics instead of collapsing into "language/wordplay".
- **Intent** — A's high accuracy (0.631) is an illusion: it stamps nearly everything *intentional* (unintentional recall 0.19). C is the balanced one (0.47 / 0.81).
- **Label reliability** — C makes 2 invalid-label errors vs. 8–9 for A/B. Few-shot examples taught it the allowed label set — which matters most for a real filter.

## The debugging story: when 0% accuracy isn't a reasoning problem

On the first run, A scored ~1% and B scored 0%. The cause was **output format, not judgment**:

| JSON parse failure | A | B | C |
|---|---|---|---|
| Before fix | 94% | 100% | 0% |
| After Ollama JSON mode | **0%** | **0%** | 0% |

- **A** wrote multi-line JSON but often stopped before the closing brace.
- **B** dropped the opening quote on the `reason` value — invalid on every single reply. The dramatic persona prompt actually *loosened* format discipline.
- **C** parsed fine from the start: its few-shot examples demonstrated one-line valid JSON, so the model copied the shape.

Fix: Ollama's `format="json"` for A and B only. C was deliberately left unconstrained so it could keep its free-text step-by-step reasoning before `FINAL: {json}` — and C went on to lead exactly the tasks that need reasoning. (JSON mode forces grammar, not values: invalid labels like `"Gender/Politics"` still occur and are tracked separately as `bad_label`.)

## Why this exists

AI now produces marketing content at unprecedented scale — but checking whether that content *fits the target culture* is still slow, manual, and inconsistent: cultural consultants, focus groups, last-minute localization QA. And because most LLMs lean toward English and Western norms, they quietly miss the nuance of everywhere else.

This system treats cultural fit not as a verdict but as a **measurable risk score** — a triage layer that flags risky drafts early so human experts only review the genuinely ambiguous cases. Human-in-the-loop by design, not a replacement for people.

## What it does

For each piece of ad copy + target culture, a local LLM (Llama 3.2 3B via Ollama, temperature 0) predicts three things in one JSON:

1. **Risk** — Expected (safe) / Normal (fittingly cultural) / Taboo (norm-breaking)
2. **Cultural topic** — religion, gender, race/ethnicity, language/wordplay, history/politics, or none
3. **Intent** — intentional / unintentional / unclear

Three prompt strategies are compared on identical items and output format:

| Version | Strategy | What it adds |
|---|---|---|
| **A** | Zero-shot (minimal) | Just label names + output format |
| **B** | Persona + pressure | A + a 20-year cultural-consultant role, high-stakes framing, label definitions, "don't judge from a Western default" rule |
| **C** | Few-shot + step-by-step | B + step-by-step instruction + 5 worked examples |

## Dataset

**84 hand-built evaluation items** mixing real ad controversies (H&M, Pepsi, Dolce & Gabbana, Nivea, Heineken, Peloton, Dove, …) with normal ads currently running (via Meta Ad Library and others), across languages including Arabic, Spanish, Japanese, German, and Hindi. Mixing failures with normal ads also tests whether the model **over-flags**.

The 8 target cultures were chosen deliberately along the **Hofstede Uncertainty Avoidance Index** — from China (UAI 30) to Japan (UAI 92) — so the follow-up dashboard (Module 2) can ask whether cultural risk tracks norm sensitivity.

Label distribution is intentionally real-world-uneven (Taboo 50 / Expected 28 / Normal 6), which is exactly why macro F1 diverges from accuracy. The 5 few-shot examples used in prompt C were removed from the scored set — the model is never tested on an item it has seen.

## Key takeaways

1. **Forcing the format is a precondition for small-model experiments.** Until parsing was fixed, A/B scores measured format failure, not reasoning.
2. **Accuracy is a trap on uneven data.** All three versions looked similar on accuracy; macro F1 and per-class recall exposed the majority-class bets.
3. **Prompt tricks aren't magic — each helps a different spot.** Few-shot lifted topic/intent/label reliability; persona balanced risk classes but destabilized format.
4. **In practice, this is an over-flagging first filter.** It errs toward blocking normal ads rather than missing risk — the right failure mode for a human-in-the-loop triage tool.

## Limitations & next steps

- **Model size:** the 3B ceiling held accuracy at 40–63%. Next: a 2×2 of {3B, 8B} × {JSON mode on} to separate format effects from scale effects.
- **Data:** 84 items is small and classes are uneven (Normal 6, Unclear 1); more items and stronger minority classes would steady macro F1.
- **Text-only:** many real controversies are visual — a multimodal setup is the natural extension.
- **Subjective labels:** inter-annotator agreement (Cohen's Kappa) across raters from the target cultures is planned to harden the gold labels.
- **Label enforcement:** an enum-constrained schema would eliminate `bad_label` at the source.

## Roadmap (the 4-module platform)

- [x] **Module 1 — this repo:** prompt-based cultural risk classification
- [ ] **Module 2 — Analytics:** cultural risk map dashboard (prediction logs × Hofstede 6D)
- [ ] **Module 3 — RAG:** grounding with NormBank / CultureBank in a local vector DB to cut hallucination and Western-default bias
- [ ] **Module 4 — Agent:** LangGraph agent mimicking the human review flow, with a human-in-the-loop approval gate and audit trail

## Repository structure

- `01_Global_Ad_Prompt_Eval.py` — runs the full evaluation grid (84 items × 3 versions), parses replies, scores accuracy / macro F1 / parse-failure / bad_label
- `prompts.py` — the three prompt strategies (`build_prompt` assembles system + user prompt per version)
- `Data/` — the 84-item evaluation dataset with gold labels (`gt_risk`, `gt_topic`, `gt_intent`)
- Results CSVs — per-item prediction logs and summary metrics (input for Module 2)

## How to run

```bash
# 1. Install Ollama and pull the model
ollama pull llama3.2:3b

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the evaluation (temperature 0, reproducible)
python 01_Global_Ad_Prompt_Eval.py
```

---

*Part of my M.Sc. AI in Business portfolio at SRH Berlin. Related project: [Cross-Lingual K-Culture RAG](https://github.com/DabinleeMe/rag-project-cross-lingual-kculture) — where the same strict-vs-loose format lesson appeared from the opposite direction.*
