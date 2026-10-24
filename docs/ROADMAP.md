# Lightcone — Team Roadmap (Narimane & Shahd)

Hackathon: IEEE Lumen 2.0 "Beyond 2030". Pitch: **Sunday 25 October, 09:00** — 5 minutes (demo included) + 5 minutes of Q&A.

---

## 1. The idea in one sentence

When people on Earth and on Mars act at almost the same moment, nobody can honestly say who was first. **Lightcone detects these "true ties" and resolves them fairly, with a receipt anyone can check, instead of letting a clock decide.**

**Pitch line:** *"On Earth, 'who was first?' is a clock question. Between planets, it's a physics question. Lightcone is the first service that answers it fairly."*

## 2. Simple comparison

Two people want the last concert ticket. One is in Tunis, the other in a distant village, and they can only send letters that take 12 minutes to arrive. Tunis says "I'll take it" at 10:00. The village says "I'll take it" at 10:05. The village person could not know about Tunis — that news arrives only at 10:12. Both acted honestly. The clock says Tunis wins, but the clock is not a fair judge here. That is exactly the Earth–Mars problem.

## 3. The future scenario (why "Beyond 2030")

| Period | What happens | Lightcone's role |
|---|---|---|
| 2030s | First crewed Mars missions; Earth and Mars teams share scarce resources (cargo mass on the next ship, rover time, antenna time) | Fair allocation between crew and Earth teams |
| 2040s | Permanent outposts, several organisations requesting the same resources | Fair booking and claims |
| 2050+ | Real Earth–Mars economy: trade, land/ice claims, contracts, votes | Fair-ordering infrastructure between planets |

Light takes **3 to 22 minutes** one way between Earth and Mars. This is physics: no future technology removes it. The problem exists from the first missions and grows with the settlement.

## 4. The problem

1. **Timestamps lie about fairness.** If two requests are made less than one light-delay apart, neither person could know about the other. Choosing by timestamp is a coin flip disguised as a rule.
2. **A central server creates built-in inequality.** Server on Earth → every Mars request arrives minutes late → Mars loses almost every race, forever. Server on Mars → Earth loses. One planet becomes second-class by design.
3. Real-world evidence: in proposals for interplanetary Bitcoin, blocks mined on Mars usually lose to Earth's because of the delay.
4. Earth already has a tiny version: high-frequency trading. Economists Budish, Cramton and Shim (2015) proposed "frequent batch auctions" so speed alone stops winning. Lightcone applies that thinking at planetary scale.

**Who suffers:** Mars settlers (structurally disadvantaged), companies selling scarce resources between planets, registries and governance bodies.

## 5. How Lightcone works (both of us must be able to explain this)

**Two nodes**, Earth and Mars. Each serves its own planet instantly. Every request is stamped **by its local node** (never by the user), so nobody can fake a time. Messages between nodes take **L seconds**, the real one-way light time for the chosen date, computed from NASA/JPL planet positions (Skyfield + DE421).

**Step 1 — Knowledge stamp (vector clock).** Each node keeps `[earth_count, mars_count]` = how many requests from each planet it has seen. A new request copies this pair. It records exactly what that node *knew* when it acted.
- A **happened before** B if A's pair ≤ B's pair on both numbers (and they differ): B's node had already seen A.
- Otherwise they are **concurrent = a TRUE TIE**.

**Step 2 — Settle in layers.** Take all unsettled requests with no unsettled request before them. One request → it gets what it asks for (if capacity remains). Several → they are a true tie → apply the fairness policy. Repeat.

**Step 3 — Fairness policies (chosen by the customer in advance).**
- **Verifiable lottery:** seed = SHA-256 of the tied requests' ids + random nonces; order = sort by hash(seed + id). Anyone can recompute it. Inside a true tie neither side could see the other's nonce — **physics itself prevents cheating**.
- **Pro-rata:** share remaining capacity in proportion to the amounts requested.
- **Priority:** medical > science > commercial, then lottery inside a class.
- **Naive mode (comparison only):** a central Earth server, first come first served — shows the unfairness we fix.

**Step 4 — Finality.** A booking is **provisional immediately** and **final after one round trip (2 × L)**. After that, the origin node is certain it has seen every request that could tie with it. Both nodes then compute the **same result independently** — shown in the UI by identical settlement hashes. No central server.

**Step 5 — Conjunction.** About every 26 months the Sun sits between Earth and Mars; NASA suspends commands while Mars is within ~2° of the Sun. Lightcone shows a warning and freezes finality.

**Every tie produces a receipt**, e.g. *"E-1 (Earth, 00:00:45) and M-1 (Mars, 00:06:27) are a true tie: news of E-1 could only reach Mars at 00:11:52, after M-1 was made. Verifiable lottery order: M-1, then E-1. Result: M-1 gets 300 kg, E-1 gets 200 kg."*

**No AI in the product core — on purpose.** A fairness decision must be deterministic and verifiable. The spec says AI is not required (§4, §17).

## 6. The SaaS product

- **Customers:** interplanetary cargo companies, Earth–Mars marketplaces, land/ice claim registries, habitat operators (power, lab time, medical equipment), governance bodies (votes, allocations).
- **They get:** an **API** (send a request → receive confirmed / provisional / tie resolved + receipt) and a **dashboard** (live link status, spacetime timeline, conflict receipts, policy settings, audit trail).
- **Deployment vision:** one Lightcone node per planet, synchronised; no planet depends on the other's server.
- **Pricing (for the pitch):** free tier for small habitats; pay per thousand decisions for companies; enterprise plans for registries and governments.

## 7. What is real vs simulated (say this honestly to the jury)

- **Real:** light-delay calculation from JPL data, vector clocks, tie detection, settlement, policies, receipts, hashes, Fairness Lab statistics.
- **Simulated:** the two planets run in one backend process (separate state, communicating only through a delayed queue), and time runs faster (×60) so a 12-minute delay fits in a 5-minute pitch. The UI says so.
- **Not built (future work):** message signatures between nodes, real network deployment over delay-tolerant networking, auctions.

---

## 8. Project structure

```
lightcone/
├── README.md  ATTRIBUTION.md  .gitignore
├── docs/ROADMAP.md (this file)  architecture.md  pitch.md
├── backend/
│   ├── requirements.txt  pytest.ini
│   ├── data/de421.bsp           JPL ephemeris (committed, works offline)
│   ├── app/
│   │   ├── main.py              API routes
│   │   ├── models.py            API contracts (Pydantic) — FROZEN
│   │   ├── link.py              distance, light delay, Sun angle
│   │   ├── clock.py             simulation clock (time compression)
│   │   ├── node.py              Earth/Mars node: log + vector clock
│   │   ├── engine.py            two nodes + delayed message queue + snapshot
│   │   ├── settle.py            tie detection + fairness policies + hash
│   │   ├── receipts.py          plain-language receipts
│   │   └── fairness.py          Monte Carlo Fairness Lab
│   └── tests/test_link.py  test_settle.py
└── frontend/
    ├── vite.config.ts           proxies /api to localhost:8000
    └── src/
        ├── App.tsx  main.tsx  index.css (colors + fonts)
        ├── types.ts             API contracts (TypeScript) — FROZEN, mirrors models.py
        ├── api.ts               fetch functions
        ├── mock/state.ts        fake true-tie state to build UI without backend
        └── components/ LinkBar  NodePanel  Spacetime  Receipts  PolicyPicker  FairnessLab
```

**Status at 00:20:** backend complete and tested (8/8 tests). Frontend scaffold ready; components are empty.

## 9. API (backend is done — this is what the frontend calls)

| Method | Route | Purpose |
|---|---|---|
| GET | `/api/link?date=YYYY-MM-DD` | distance, one-way/round-trip delay, Sun angle, conjunction |
| POST | `/api/scenario` | `{date, compression, resource:{name,capacity,unit,divisible}, policy}` → resets with new settings, returns state |
| POST | `/api/request` | `{node:"earth"/"mars", actor, qty, priority}` → the new request |
| GET | `/api/state` | full state: sim time, both nodes (log, allocations, hash), messages in flight, receipts, naive result |
| POST | `/api/reset` | clear all requests, keep settings |
| GET | `/api/fairness?date=&trials=10000` | Mars win rate: Earth server vs Mars server vs Lightcone, + tie rate |

Full field lists: `frontend/src/types.ts`. Example data: `frontend/src/mock/state.ts`.

## 10. How to run (Windows PowerShell)

**First time (Shahd):**
```powershell
cd $HOME
git clone https://github.com/Narimane-Mezned/lightcone.git
cd lightcone\backend
python -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m pytest
cd ..\frontend
npm install
```

**Every time — window 1 (backend):**
```powershell
cd $HOME\lightcone\backend
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8000
```
Check: http://localhost:8000/docs (interactive API page).

**Every time — window 2 (frontend):**
```powershell
cd $HOME\lightcone\frontend
npm run dev
```
Open http://localhost:5173

**Git, every hour at least:**
```powershell
git pull --rebase
git add .
git commit -m "what you did"
git push
```
PowerShell rules: no `&&`, no `rm -rf`, no `source`, no `mkdir -p`.

## 11. Who does what

**Ownership to avoid Git conflicts:** each person edits only their own files. `models.py` and `types.ts` change only if both agree out loud.

**Narimane** — backend owner (done) + three frontend components:
- `components/Receipts.tsx` — list of receipts: explanation, seed, order, allocations.
- `components/PolicyPicker.tsx` — lottery / pro-rata / priority + date + Reset; calls `/api/scenario` and `/api/reset`.
- `components/FairnessLab.tsx` — 3 bars (Mars win rate: Earth server / Mars server / Lightcone) + tie rate, plain SVG; calls `/api/fairness`.
- Backend fixes if Shahd needs anything; `docs/architecture.md`; README; 3 demo scenarios; pitch Q&A preparation.

**Shahd** — main screen and the wow moment:
- `App.tsx` — layout, polling `api.state()` every 500 ms, passes state to components. Layout: link bar on top; Earth panel left, spacetime diagram centre, Mars panel right; tabs at bottom (Receipts / Policy / Fairness Lab / Naive vs Lightcone).
- `components/LinkBar.tsx` — "EARTH ⟷ MARS · 1.38 AU · light delay 11 m 29 s · round trip 22 m 58 s · simulation ×60", conjunction warning.
- `components/NodePanel.tsx` — Earth (blue) / Mars (rust): actor, quantity (kg), priority, **Book** button (calls `/api/request`); below: that node's allocations + hash.
- `components/Spacetime.tsx` — **the heart of the demo.** SVG: Earth vertical line left, Mars right, time going down. Each request = a dot. Each message = a gold line from (origin, sent_t) to (destination, arrive_t); if not delivered yet, draw only up to the current time so it "travels". Requests in a receipt's `tie` glow violet with a "TRUE TIE" label. Provisional = dashed circle, final = solid green. A horizontal "now" line moves down.
- Naive vs Lightcone toggle (shows `naive_allocations` next to the real ones).
- Slides (6) + backup demo video.

**Design system** (already in `index.css` as Tailwind colors): `bg-ink` background, `bg-panel` panels, `text-text`, `text-muted`, `earth` #4EA8FF, `mars` #E0603A, `signal` (gold, light signals) #F5D27A, `tie` (violet) #B79CFF, `final` (green) #3FB950. Fonts: Inter (`font-sans`), JetBrains Mono for numbers/times/hashes (`font-mono`). No glassmorphism, no gradients, no generic stat cards.

## 12. Timeline

| Time | Narimane | Shahd | Checkpoint |
|---|---|---|---|
| 00:20–00:45 | Push backend + roadmap | Clone, install, run both servers, read this file | Both see the app at :5173 |
| 00:45–02:15 | Receipts, PolicyPicker, FairnessLab (on mock data first) | App layout, LinkBar, NodePanel, Spacetime on `mockState` | — |
| **02:15** | Merge, test together | Same | **Real end-to-end: book on Earth + Mars → TRUE TIE on screen** |
| 02:15–04:15 | Connect components to live API, demo scenarios, architecture doc | Live polling, animations, tie highlight, naive toggle | — |
| **04:15** | Explain the frontend aloud | Explain the algorithm aloud | Understanding check. If animation is buggy → redraw each poll without animation |
| 04:15–06:00 | README, edge cases, Q&A prep | Polish all states (empty, loading, error, conjunction), slides start | — |
| **06:00** | — | — | **FEATURE FREEZE — only bug fixes after this** |
| 06:00–07:15 | 5 full test runs, fixes | Slides + record backup video | — |
| 07:15–08:20 | Pitch rehearsal ×3 + Q&A drill | Same | — |
| 08:20–09:00 | Buffer, travel, laptop charged, servers started, one reset | Same | **09:00 pitch** |

## 13. Demo script (5 minutes)

**0:00–1:20 — Story.** "It's 2040. A Mars settlement and companies on Earth all need space on the next cargo ship. Light takes up to 22 minutes between the planets. When an Earth buyer and a Mars buyer book the last space four minutes apart, neither could have known about the other. Every system today picks a winner by timestamp through a central server. Put that server on Earth and Mars loses almost every race — because of physics, not fairness. We call these moments true ties, and we built Lightcone to resolve them fairly."

**1:20–4:20 — Live demo.**
1. Link bar: real distance from JPL data, light delay, ×60 simulation speed.
2. Book 400 kg from Earth (Helios Freight).
3. Book 300 kg from Mars (Jezero Clinic) a few simulated minutes later. The gold line from Earth is still travelling.
4. When the news arrives: violet **TRUE TIE**. Receipt explains why.
5. Toggle naive: the Earth server gives Earth everything. Toggle back: verifiable lottery result.
6. After one round trip both turn green — Earth and Mars hashes identical, no central server.
7. Switch policy to pro-rata: the customer chooses the rule.
8. Fairness Lab: "Over 10,000 simulated races, Mars wins X% with an Earth server and Y% with Lightcone" (use the real numbers on screen).

**4:20–5:00 — Close.** "Lightcone is an API and dashboard for cargo operators, claim registries and habitat schedulers. The speed of light will never change, so the rules of fairness have to."

## 14. Q&A preparation

1. **"Isn't this just vector clocks?"** Vector clocks only tell you two events are concurrent. Our contribution is what comes after: turning concurrency into fair allocation, with physics-based finality, a cheat-proof lottery and receipts.
2. **"Why not a blockchain?"** Blockchains make nodes agree on one history; longest-chain rules favour the better-connected side (Earth). We decide what's fair among simultaneous claims. Complementary.
3. **"Can someone backdate?"** No. Requests are stamped by their local node, and order comes from what each node had received, not from clocks. Signing node messages is the next step.
4. **"Why does finality take a round trip?"** It's the physical minimum. Anything faster is either unfair or still provisional. We show provisional status immediately.
5. **"Why no AI?"** Fairness must be deterministic and verifiable by anyone.
6. **"Limits?"** Two nodes simulated in one process, no message signing yet, lottery/pro-rata/priority rather than full auctions, conjunction threshold uses NASA's ~2° practice.

## 15. Credits (Rule 12.4) — see ATTRIBUTION.md

Skyfield (MIT), JPL DE421, FastAPI, React, Vite, Tailwind, Framer Motion, Inter & JetBrains Mono fonts. Concepts: Lamport clocks (1978), vector clocks (Fidge & Mattern, 1988), frequent batch auctions (Budish, Cramton & Shim, 2015). AI tools helped with planning and code; we can explain all of it.
