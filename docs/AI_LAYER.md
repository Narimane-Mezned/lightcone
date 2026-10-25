# Lightcone — The AI Layer

**Principle: AI at the edge, determinism at the core.** AI understands people, negotiates for them and predicts what light hasn't delivered yet. The final decision is still a deterministic computation that both planets run independently and anyone can recompute.

## 0. The story in one table

Every AI feature answers something the speed of light makes impossible for humans:

| Physics makes it impossible to… | Lightcone's AI answer |
|---|---|
| …explain your needs in time | **Intent compiler** (LLM): plain language → envoy mandate |
| …negotiate in time (each exchange costs ~23 min) | **AI envoys**: negotiate instantly for you (Nash bargaining) |
| …see the other planet's present (its last ~11 minutes are still in space) | **Ghost Radar** (ML): predicts requests already travelling toward you |
| …read a decision in your own terms | **Envoy transcript** (LLM) with a number guardrail |

Pitch line: *"You can't negotiate across 20 light-minutes, so your request carries an AI envoy. And you can't see the other planet's present, so an ML radar shows you what light hasn't delivered yet."*

## 1. Intent compiler — `backend/app/intent.py`, `POST /api/intent`

The requester writes, for example:
- Mars: *"We need at least 250 kg of medical supplies before the March launch window. Anything above 300 kg is useless."*
- Earth: *"We would like 400 kg of cargo space. We can wait for the next ship for part of it, and we can give up 50 kg for a medical emergency."*

The LLM (Llama 3.3 70B on Groq, temperature 0, JSON mode) compiles an **envoy mandate**:

| Field | Meaning |
|---|---|
| `min_qty`, `max_qty` | smallest useful amount, largest useful amount |
| `category` | medical / science / commercial (the requester's own purpose) |
| `can_defer` | can it wait for the next ship? |
| `next_ship_value` | how much 1 kg on the next ship is worth vs 1 kg now (0–100%) |
| `yield_to_medical`, `yield_max_qty` | will it give up some cargo for a medical need, and how much |

**Guardrails:** every quantity must literally appear in the text (no invented numbers); invalid ranges are rejected. **The human confirms**: all fields are editable before booking. **Fallback:** a rule-based parser (regular expressions) takes over if there is no key, no internet, or the guardrail rejects the answer. The UI always shows which one understood the need.

## 2. AI envoys — `backend/app/settle.py` (`_envoys`), policy `envoys` (default)

When a true tie happens, each request's envoy represents its owner. The negotiation is **game theory, not a chat**, so both planets reach exactly the same deal.

1. **Utility of each envoy** for an outcome (now, next ship):
   `u = (min(now, max) + next_ship_value × next_ship_kg) / max`, divided by 4 if the outcome is below the (effective) minimum. A requester that yields 50 kg to medical has an effective minimum 50 kg lower when the other side is medical.
2. **Disagreement point** = each envoy's expected utility under the verifiable lottery (the average over all lottery orders). An envoy never accepts a deal worse than a coin flip.
3. **Deals considered**: every split of the capacity in steps of 2% (2 or 3 envoys); any envoy that can wait gets a guaranteed next-ship slot for the shortfall to its minimum.
4. **Chosen deal**: the one maximising the **product of the gains** over the lottery: the **Nash bargaining solution** (John Nash, 1950). It is fair (symmetric, nobody worse off than the default) and efficient.
5. If no deal beats the lottery for everyone, it falls back to the needs-aware rule.

Demo result (500 kg): Jezero Clinic gets **300 kg now (100% of its ideal vs 54% from a lottery)**; Helios Freight gets **200 kg now + 150 kg guaranteed on the next ship (76% vs 56%)**. **Both are better off than with a coin flip.** Needs met: **2/2 vs 1/2** for the lottery (which can give the clinic 100 kg, below its minimum).

Determinism: the computation uses only data both planets have after the round trip, with fixed rounding and tie-breaking, so both hashes match.

## 3. Ghost Radar (ML) — `backend/app/ghost.py`, `backend/train_ghost.py`

**Problem:** each planet is blind to the other's last L minutes (L ≈ 11 min in the demo). Any request made there is still travelling.

**Model:** a **Poisson regression** (generalised linear model, trained with Newton–Raphson / IRLS in NumPy) predicting booking requests per 10-minute bin from 9 features: time of sol (sin/cos, two harmonics), days to the launch window (two exponential "rush" terms + linear), planet.

**Training data:** one **simulated** year of Earth and Mars colony traffic (107,310 bins) with daily cycles and a booking rush before the launch window. It is synthetic because no real interplanetary traffic exists yet; we say so. `python train_ghost.py` regenerates the model and prints the metrics.

**Evaluation on held-out data** (20%):
- demand-rate error **0.0038** vs **0.0708** for a constant-rate assumption (about 19× better)
- during the pre-launch rush: **0.035** vs **0.345** (about 10× better)
- per-bin deviance explained 6.3%: individual 10-minute counts are dominated by randomness; the model's job is the underlying rate, which it recovers well.

**What the user sees:**
- On the diagram: a violet **"unseen by Earth / unseen by Mars" zone** and **ghost dots** where the radar expects requests already in flight.
- In each panel: expected unseen requests, chance of at least one, and for your provisional booking a **"likely final" range** (computed by re-running the settlement with a predicted ghost request).
- When a real request arrives: **"arrived · radar said 65%"**, prediction vs reality on screen.

## 4. Envoy transcript (LLM) — `backend/app/narrate.py`

After the deal, the LLM writes a short dialogue between the envoys ("Envoy for Jezero Clinic: …") and a final "Deal:" line, from the decision data only. **Guardrail:** every number in the text must exist in the decision data, otherwise the text is discarded and a template explanation is shown. Runs in a background thread, cached, so the 500 ms polling never waits for the AI.

## 5. Setup

1. Free API key: console.groq.com → API Keys → Create.
2. Create `backend\.env` in PowerShell (never commit it; `.gitignore` blocks it):
   ```powershell
   Set-Content -Path "$HOME\lightcone\backend\.env" -Value "GROQ_API_KEY=gsk_..." -Encoding ascii
   ```
3. Optional settings in `.env`: `LLM_MODEL=llama-3.3-70b-versatile`, `LLM_TIMEOUT_S=8`, `LIGHTCONE_OFFLINE=1` (forces the fallback — rehearse the offline backup once).
4. `pip install -r requirements.txt`, restart uvicorn. Policy tab shows "AI: online".

## 6. Demo flow (5 minutes)

1. **Story (1:20):** the future, the true tie, and *"you can't negotiate across 20 light-minutes."*
2. **Mars panel:** the clinic's sentence → **Understand my need** → mandate appears (250–300 kg, medical, cannot wait). *"AI turns words into a mandate; the human confirms."*
3. **Earth panel:** the freight sentence → Understand → 400 kg, can wait (next ship worth 70%), yields 50 kg to medical.
4. Point at **Ghost Radar**: *"Earth can't see Mars's last 11 minutes, but the ML radar estimates a 51% chance a Mars request is already on its way."*
5. **Book Earth, then Mars within ~4 s.** Gold lines travel; ghosts sit in the unseen zone. When news arrives: **TRUE TIE**, and *"radar said 65%"*.
6. **Receipts tab:** the envoy transcript; the two envoy cards (**+20 and +46 points over a lottery**); the table **Lightcone 2/2 needs met vs lottery 1/2**.
7. Both hashes identical: *"both planets computed the same deal independently: no central server."*
8. **Fairness Lab** (Earth server vs Lightcone) and the **Ghost Radar model card** (Policy tab) if time allows.

## 7. Q&A on the AI

- **"Why AI?"** Physics removes negotiation and visibility. Envoys restore negotiation; the radar restores (probabilistic) visibility. Without AI, the system can only flip coins.
- **"Can an LLM decide unfairly?"** The LLM never decides. It compiles a mandate the human confirms, and writes a transcript checked against the numbers. The deal itself is Nash bargaining: deterministic, auditable, identical on both planets.
- **"Why Nash bargaining?"** It is the standard axiomatic solution for two-party bargaining: nobody gets less than their no-deal outcome (here, the lottery), it is symmetric, and it is Pareto-efficient.
- **"Your ML model is trained on fake data."** Yes, simulated, because no Mars traffic exists. The method (a Poisson GLM on time-of-sol and launch-window features) is real and would be retrained on real traffic logs from day one. We report held-out metrics and its limits.
- **"Can people lie in their mandate?"** Yes, like any declared need. Mitigations: mandates are recorded and auditable, medical claims can require certification, and the next-ship guarantee reduces the incentive to exaggerate. Anomaly detection on mandates is our next step.
- **"What if the AI is down on Mars?"** The rule-based fallback runs locally and the decision logic needs no AI. Long term, a small local model on each planet; the code only needs an OpenAI-compatible endpoint.
- **"Which model and prompts?"** Llama 3.3 70B via Groq, temperature 0, JSON mode. Prompts: `SYSTEM` in `intent.py`, `SYSTEM` and `ENVOY_SYSTEM` in `narrate.py`.

## 8. Files

| File | Role |
|---|---|
| `backend/app/llm.py` | Groq client (OpenAI-compatible), reads the key from `.env` |
| `backend/app/intent.py` | Intent compiler: LLM + guardrail + rule-based fallback |
| `backend/app/settle.py` | Tie detection, envoys (Nash bargaining), needs-aware, lottery, pro-rata, priority |
| `backend/app/narrate.py` | Envoy transcripts and decision letters + guardrail + background cache |
| `backend/app/ghost.py` | Ghost Radar inference (expected unseen requests, ghost positions) |
| `backend/app/ghost_model.json` | Trained model coefficients + evaluation metrics |
| `backend/train_ghost.py` | Synthetic traffic generator + Poisson regression training + evaluation |
| `backend/app/engine.py` | Nodes, delayed messages, radar per node, "likely final" forecasts, prediction-vs-reality |
| `backend/tests/test_ai.py` | Tests: parser, envoys beat lottery, radar, forecasts, guardrail |
| `frontend/src/components/NodePanel.tsx` | Plain-language need, envoy mandate editor, Ghost Radar panel |
| `frontend/src/components/Spacetime.tsx` | Unseen zones, ghost dots, "radar said X%" on arrival |
| `frontend/src/components/Receipts.tsx` | Envoy transcript, envoy gain cards, Lightcone vs lottery table |
| `frontend/src/components/PolicyPicker.tsx` | Policies (envoys default), AI status, Ghost Radar model card |
