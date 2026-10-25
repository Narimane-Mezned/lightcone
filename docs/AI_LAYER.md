# Lightcone — The AI Layer

**Principle: AI at the edge, determinism at the core.** AI understands humans; it never decides. The decision is a deterministic algorithm anyone can recompute.

## 1. Why Lightcone needs AI (the argument for the jury)

Between Earth and Mars, every exchange costs a full light round trip: 7 to 44 minutes. So when two requests tie, **the requesters cannot negotiate** — one question and its answer could take most of an hour. A blind lottery is fair but can be absurd: it can give a Mars clinic 100 kg when it needs at least 250 kg, while a freight company that could easily wait gets everything.

The fix: **each request must carry its owner's real needs**, because the owner can't be asked later. People express needs in plain language. AI turns that language into constraints the algorithm can use.

## 2. The four AI features

### 2.1 Intent compiler (`backend/app/intent.py`, route `POST /api/intent`)
- The requester writes: *"We need at least 250 kg of medical supplies before the March launch window. Anything above 300 kg is useless."*
- An LLM (Llama 3.3 70B on Groq, temperature 0, JSON output) returns: `min 250 · max 300 · medical · cannot wait for the next ship` + a one-line summary.
- **Guardrail:** the backend rejects any quantity the LLM produces that does not literally appear in the text (no invented numbers), and any invalid range.
- **The human confirms**: the constraints are shown as editable fields before booking. AI proposes, the human decides.
- **Fallback:** if there is no API key, no internet, or the guardrail rejects the answer, a rule-based parser (regular expressions for "at least", "up to", "can wait", medical/science keywords) takes over. The demo never breaks. The UI shows which one was used.

### 2.2 Needs-aware fairness (`backend/app/settle.py`, policy `needs`) — deterministic, no AI
For a true tie with capacity C:
1. Order the tied requests: requests that **cannot wait** first, then medical > science > commercial, then the verifiable lottery.
2. Give each request its **minimum** if capacity allows.
3. Share what is left by **max-min fairness** (water-filling: equal shares, capped at each request's maximum).
4. Any request that **can wait** and did not reach its minimum gets a **guaranteed priority slot on the next ship** for the missing amount.
5. Measure **needs met** (requests that reach their minimum now or with the guarantee) and compare with what the plain lottery would have done.

Demo result (capacity 500 kg): lottery → Freight 400, Clinic 100 (below its minimum: **1/2 needs met**). Lightcone → Clinic 300, Freight 200 now + 200 guaranteed next ship (**2/2 needs met**).

Both planets still compute the decision independently and get the same hash.

### 2.3 AI-written decision letters with a number guardrail (`backend/app/narrate.py`)
- After a tie, an LLM writes a short, human explanation for the requesters from the decision data (JSON facts).
- **Guardrail:** every number in the AI text must exist in the decision data; otherwise the text is discarded and a template explanation is shown. The UI says "every number checked against the decision".
- Runs in a background thread and is cached, so the 500 ms polling never waits for the AI.

### 2.4 Tie-risk forecast (`backend/app/engine.py`, `tie_risk` per node) — statistics, not ML
Each planet sees the probability that a request it sends now collides with one from the other planet that it cannot see yet. Model: requests from the other planet arrive as a Poisson process with rate λ (estimated from observed requests); a collision happens if one falls within ±L of now, so `risk = 1 − exp(−λ · 2L)`.

## 3. Setup

1. Free API key: console.groq.com → API Keys → Create.
2. File `backend\.env` (already ignored by Git — never commit it):
   ```
   GROQ_API_KEY=gsk_...
   ```
3. Optional: `LLM_MODEL=llama-3.3-70b-versatile` (default), `LLM_TIMEOUT_S=8`, `LIGHTCONE_OFFLINE=1` to force the rule-based fallback (rehearse the offline backup).
4. `pip install -r requirements.txt` (adds `python-dotenv`), restart uvicorn.

Check: Policy tab shows "AI: online". Click "Understand my need" → the badge says "understood by AI · llama-3.3-70b-versatile".

## 4. New demo flow (replaces steps 2–5 of the pitch demo)

1. Mars panel: show the clinic's sentence → **Understand my need** → constraints appear (min 250, max 300, medical, cannot wait). "AI understands the need; the human confirms it."
2. Earth panel: freight sentence → Understand → 400 kg, can wait.
3. Book Earth, then Mars within a few seconds → gold lines travel → **TRUE TIE**.
4. Receipts tab: the AI letter + the comparison table: **Lightcone 2/2 needs met vs lottery 1/2**. "A lottery would have given the clinic 100 kg — useless. Lightcone gives it 300 kg and guarantees the freight company its cargo on the next ship."
5. Both hashes identical → agreement without a central server.
6. Fairness Lab → Earth server 20% vs Lightcone 51% (read the real numbers on screen).

## 5. Q&A on the AI

- **"Why use AI?"** Light delay makes negotiation impossible, so the request must carry its owner's needs. People state needs in natural language; AI turns them into constraints. Without it, fairness is blind.
- **"Can the AI make a wrong decision?"** The AI never decides. It proposes constraints the human confirms, and a deterministic algorithm decides. Guardrails reject invented numbers both on the way in (intent) and on the way out (letters).
- **"What if the AI is down on Mars?"** Rule-based fallback, automatically. Long term, a small model runs locally on each planet — the code only needs an OpenAI-compatible endpoint.
- **"Can people lie about their needs?"** Yes, like any declared need. Mitigations: needs are signed and auditable after the fact, categories like medical can require certification, and the next-ship guarantee reduces the incentive to exaggerate. Abuse detection is future work.
- **"Which model, which prompt?"** Llama 3.3 70B via Groq, temperature 0, JSON mode. Prompts are in `intent.py` (SYSTEM) and `narrate.py` (SYSTEM).

## 6. Files

| File | Role |
|---|---|
| `backend/app/llm.py` | Groq client (OpenAI-compatible API), reads the key from `.env` |
| `backend/app/intent.py` | Intent compiler: LLM + number guardrail + rule-based fallback |
| `backend/app/narrate.py` | AI decision letters + number guardrail + background cache |
| `backend/app/settle.py` | Adds the deterministic `needs` policy and the lottery comparison |
| `backend/app/receipts.py` | Receipts with deferred slots, needs met, lottery comparison, AI letter |
| `backend/tests/test_ai.py` | Tests: parser, needs-aware result, tie risk, guardrail |
| `frontend/src/components/NodePanel.tsx` | Plain-language need, "Understand my need", editable constraints, tie risk |
| `frontend/src/components/Receipts.tsx` | AI letter + Lightcone vs lottery table |
| `frontend/src/components/PolicyPicker.tsx` | Four policies (needs-aware default), date, capacity, AI status |
| `frontend/src/components/FairnessLab.tsx` | 10,000-race simulation bars |
