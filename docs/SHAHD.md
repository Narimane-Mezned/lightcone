# Shahd — Your Lightcone Guide (everything you need tonight)

> **UPDATE 01:20 — AI layer added.** Lightcone now has AI envoys (negotiate for each requester by Nash bargaining), an intent compiler (plain language → mandate), Ghost Radar (ML prediction of requests still in flight) and guarded AI transcripts. **Read `docs/AI_LAYER.md`: its demo flow (section 6) and Q&A (section 7) replace the older ones in this file.**

Pitch: **Sunday 25 October, 09:00**. 5 minutes including the live demo, then 5 minutes of Q&A.
Repo: https://github.com/Narimane-Mezned/lightcone

Read this file first, then `docs/ROADMAP.md` (the full idea, algorithm and Q&A) and `docs/FRONTEND_GUIDE.md` (how the frontend pieces connect).

---

## 1. Lightcone in 30 seconds

Light takes 3 to 22 minutes between Earth and Mars. When an Earth buyer and a Mars buyer book the last cargo space a few minutes apart, **neither could have known about the other** — the news hadn't arrived yet. We call this a **TRUE TIE**. Today's systems pick a winner by timestamp on a central server, and a server on Earth makes Mars lose almost every race because of physics, not fairness. **Lightcone detects true ties and resolves them fairly, with a receipt anyone can check.**

Pitch line: *"On Earth, 'who was first?' is a clock question. Between planets, it's a physics question."*

---

## 2. Setup (Windows PowerShell — one command per line)

PowerShell rules: never use `&&`, `rm -rf`, `source` or `mkdir -p` (those are Linux commands).

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

`python -m pytest` must show `9 passed`.

## 3. Run the app (every time)

**PowerShell window 1 — backend:**
```powershell
cd $HOME\lightcone\backend
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8000
```

**PowerShell window 2 — frontend:**
```powershell
cd $HOME\lightcone\frontend
npm run dev
```

Open **http://localhost:5173**. API test page: http://localhost:8000/docs

## 4. Git (at least every hour)

```powershell
cd $HOME\lightcone
git pull --rebase
git add .
git commit -m "describe what you changed"
git push
```

**You own:** `frontend/src/App.tsx`, `components/LinkBar.tsx`, `components/NodePanel.tsx`, `components/Spacetime.tsx`, the slides and the backup video.
**Narimane owns:** everything in `backend/`, `components/Receipts.tsx`, `components/PolicyPicker.tsx`, `components/FairnessLab.tsx`, and the docs.
Only edit your own files → no Git conflicts.

---

## 5. What is already done

- **Backend:** complete and tested (true-tie detection, policies, receipts, Fairness Lab).
- **Your 4 files are already written and working:** `App.tsx` (layout + polling every 500 ms + error banner + tabs), `LinkBar.tsx` (distance, light delay, round trip, sim time, conjunction warning), `NodePanel.tsx` (booking form + what each node knows + hash), `Spacetime.tsx` (the diagram).
- Narimane is building Receipts, Policy and Fairness Lab tabs.

So your job tonight is: **understand your files, test them live, polish, and own the slides, video and demo.**

### Work without the backend
In `App.tsx`, set `const USE_MOCK = true` to see a ready-made true tie (from `mock/state.ts`). **Set it back to `false` before committing.**

---

## 6. Understand your files (so you can answer the jury)

**`App.tsx`**
- `useEffect` #1 loads `/api/link` when the date changes (distance, Sun angle).
- `useEffect` #2 calls `api.state()` every 500 ms → `state`. That's why the diagram moves: the backend's simulation clock runs 60× faster than real time.
- Renders: LinkBar → [Earth panel | Spacetime | Mars panel] → tabs.

**`NodePanel.tsx`**
- Form: requester, cargo kg, priority → **Book** calls `POST /api/request` with `node = "earth"` or `"mars"`.
- "What this node knows" = that node's own settlement (`state.nodes[node].allocations`). Earth and Mars can temporarily disagree — because news hasn't arrived yet. After one round trip they agree, and the **settlement hash** at the bottom becomes identical on both sides. That proves agreement **without a central server**.
- `vc [a, b]` = the node's vector clock: how many Earth and Mars requests it has seen.

**`Spacetime.tsx`** (the wow visual)
- Blue vertical line = Earth, rust line = Mars, **time flows down**.
- `y(t) = 50 + (t - t0) / span * 490`, with `span = max(4 × light delay, 600 s)`; the window scrolls once time passes `span`.
- Each request = a dot. Dashed = provisional, green = final (after one round trip), amber = frozen (conjunction).
- **Gold line** = the news of a request travelling at light speed, from (sender, sent time) to (receiver, arrival time). If not yet delivered, it is drawn only up to "now", with a gold dot at its head — that's why you see it travel.
- **Violet glow + TRUE TIE** = the requests listed in a receipt: two requests with **no gold line reaching either one before it was made**.
- Dashed horizontal line = now.

---

## 7. Your timeline

| Time | Task | Done when |
|---|---|---|
| 00:45–01:15 | Setup (section 2), run (section 3), read this file + ROADMAP sections 1–7 | App visible at :5173 |
| 01:15–01:45 | Live test (section 8, scenarios A and B). Note anything that looks wrong or ugly | You've seen a TRUE TIE appear live |
| 01:45–02:15 | Read your 4 files with section 6 open. Ask Narimane or Claude about any line you don't understand | You can explain Spacetime's math aloud |
| **02:15** | **Checkpoint with Narimane:** pull, run the full flow together | Book Earth + Mars → TRUE TIE on diagram and in Receipts tab |
| 02:15–04:15 | Polish (section 9) | Every item checked |
| **04:15** | **Swap:** you explain the algorithm to Narimane (ROADMAP section 5), she explains the frontend | Both fluent |
| 04:30–06:00 | Slides (section 10) | 6 slides done |
| **06:00** | **FEATURE FREEZE** — only bug fixes | — |
| 06:00–07:15 | Backup video + screenshots (section 11); 3 full demo runs | Video saved on desktop |
| 07:15–08:20 | Pitch rehearsal ×3 with a 5-min timer (section 12), Q&A drill | Under 5:00 every time |
| 08:20–09:00 | Laptop charged, both servers running, slides + video open, one Reset before going on stage | 09:00 pitch |

---

## 8. Live test scenarios

Light delay ≈ 11.5 min for 2040-01-01. At ×60, that is **about 11.5 real seconds**; a round trip ≈ 23 real seconds.

**Scenario A — ordered (no tie):** click Book from Earth → wait until the gold line reaches Mars (~12 s) → click Book from Mars. Result: no tie, Earth served first (400 kg), Mars gets the remaining 100 kg.

**Scenario B — TRUE TIE (the main demo):** Reset (Policy tab, or `POST /api/reset` on /docs) → click Book from Earth (Helios Freight, 400 kg) → **within ~4 seconds** click Book from Mars (Jezero Clinic, 300 kg) → both gold lines travel → when they arrive, both dots glow violet with **TRUE TIE**; the Receipts tab explains why. After ~23 s both dots turn green and the two hashes match.

**Naive comparison:** open the "Naive vs Lightcone" tab: the central Earth server gives Earth all 400 kg; Lightcone resolves the tie by the verifiable lottery.

---

## 9. Polish checklist (02:15–04:15)

- [ ] Test at the projector resolution (likely 1280×720 or 1920×1080). Use browser zoom (Ctrl + / Ctrl −) to check readability from 3 metres away. If too small, increase font sizes in Spacetime (`fontSize`) and NodePanel.
- [ ] TRUE TIE label readable and not overlapping dots (adjust the `rect` width/position in Spacetime if needed).
- [ ] Book button: double-clicking does not create two requests by mistake (it is disabled while booking — verify).
- [ ] Empty state: when there are no requests, the diagram is clean (only planets, time ticks and "now").
- [ ] Error banner: stop the backend (Ctrl+C) → red banner appears; restart → it disappears.
- [ ] "Naive vs Lightcone" tab (in App.tsx): make it look clean — two columns, the naive side labelled "Central Earth server (first come, first served)".
- [ ] Optional only if everything else is done: smoother animation. The 500 ms polling already moves the gold lines; do not risk breaking the demo.

---

## 10. Slides (6 slides, dark background #0B0D12, same colours as the app)

1. **The future (2040).** "A Mars settlement and Earth companies share scarce resources — like space on the next cargo ship." Visual: Earth and Mars with "3–22 min light delay".
2. **The problem: the true tie.** "Earth books at 10:00. Mars books at 10:05. The news from Earth reaches Mars at 10:12. Who was first?" Then: "A central server on Earth makes Mars lose almost every race — inequality caused by physics."
3. **The solution: Lightcone.** "Detects true ties. Resolves them with a fair rule chosen in advance. Gives a verifiable receipt." Screenshot of the app with a TRUE TIE.
4. **How it works.** Vector clocks ("what each planet knew") → settle in layers → fairness policy (verifiable lottery / pro-rata / priority) → final after one round trip, both planets compute the same result (identical hashes). Real light delay from NASA/JPL data. No AI in the core: fairness must be deterministic and checkable.
5. **Impact: Fairness Lab.** Bar chart: Mars win rate with an Earth server vs Lightcone (ask Narimane for the real numbers from the app). "Over 10,000 simulated races."
6. **The product.** API + dashboard for cargo operators, claim registries, habitat schedulers. Free tier for small habitats, pay per decision for companies. "The speed of light will never change, so the rules of fairness have to."

Keep text minimal; the live demo carries the story. Add credits in small text on slide 4 or 6: Skyfield, NASA/JPL DE421, FastAPI, React.

## 11. Backup video and screenshots

- **Video (Windows):** open the app in Chrome full screen → press **Win + Alt + R** (Xbox Game Bar) to start/stop recording → run scenario B fully (~45 s). The file goes to `Videos\Captures`. Copy it to the desktop.
- **Screenshots:** **Win + Shift + S**. Take: (1) TRUE TIE on the diagram, (2) the Receipts tab, (3) the Fairness Lab bars, (4) Naive vs Lightcone.

## 12. Pitch split (suggested)

- **Shahd (0:00–1:20):** the story — future, problem, true tie (slides 1–3).
- **Shahd drives the demo (1:20–4:20)** while **Narimane narrates** the technical part:
  1. Link bar: real distance from JPL data, light delay, ×60 simulation.
  2. Book Earth 400 kg → book Mars 300 kg ~4 s later → gold lines travel.
  3. TRUE TIE appears → Receipts tab: the explanation.
  4. Naive tab: the Earth server gives Earth everything.
  5. Wait for green: identical hashes — agreement without a central server.
  6. Policy → pro-rata (optional if time allows).
  7. Fairness Lab numbers.
- **Narimane (4:20–5:00):** the product and the closing line.
- **Q&A:** Narimane leads on the algorithm; Shahd answers on the interface, users and the product. Learn ROADMAP section 14.

## 13. Troubleshooting

| Problem | Fix |
|---|---|
| Red banner "Backend unreachable" | Window 1 must show `Application startup complete`. Restart it with section 3. |
| `uvicorn` not recognised | Activate the venv first: `.venv\Scripts\Activate.ps1` |
| Activate.ps1 blocked | Run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` first |
| Port already in use | Close the other terminal running it, or restart the PC terminal |
| `git push` rejected | `git pull --rebase` then `git push` |
| Page blank | Check window 2 for errors; run `npx tsc --noEmit` in `frontend` to see TypeScript errors |
| Anything else | Copy the error and send it to Narimane / Claude |
