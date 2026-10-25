# Lightcone — Frontend Guide (Shahd & Narimane)

> **UPDATE 01:20 — AI layer added.** Lightcone now has AI envoys (negotiate for each requester by Nash bargaining), an intent compiler (plain language → mandate), Ghost Radar (ML prediction of requests still in flight) and guarded AI transcripts. **Read `docs/AI_LAYER.md`: its demo flow (section 6) and Q&A (section 7) replace the older ones in this file.**

Read `docs/ROADMAP.md` first for the idea. This file explains exactly how the frontend fits together.

## 1. How the pieces connect

`App.tsx` is already written. It:
- loads the link info (`/api/link`) whenever the date changes,
- polls `/api/state` every 500 ms and keeps the result in `state`,
- shows an error banner if the backend is down,
- renders the layout: LinkBar on top → Earth panel | Spacetime | Mars panel → tabs (Receipts / Policy / Fairness Lab / Naive vs Lightcone).

**To work without the backend:** set `const USE_MOCK = true` at the top of `App.tsx`. It then uses `mock/state.ts` (a ready-made true tie). Set it back to `false` before committing.

Every component already exists as a skeleton with its **final props**. Do not change the props without telling the other person — that is the contract between your files.

## 2. Component contracts and owners

| Component | Owner | Props (already defined) | What it must do |
|---|---|---|---|
| `LinkBar.tsx` | Shahd | `link`, `state`, `date`, `onDateChange` | Show `EARTH ⟷ MARS · {distance_au} AU · light delay {mm} m {ss} s · round trip … · simulation ×{compression}`. If `link.conjunction` is true: amber style + "Solar conjunction — finality paused". |
| `NodePanel.tsx` | Shahd | `node` ("earth"/"mars"), `state`, `onBooked` | Form: actor (text), quantity (number, kg), priority (medical/science/commercial), **Book** button → `api.request({node, actor, qty, priority})` then `onBooked()`. Below: this node's `allocations` (id → kg) and first 12 chars of `hash`. Title colour: `text-earth` or `text-mars`. Suggested defaults: Earth actor "Helios Freight" 400 kg; Mars actor "Jezero Clinic" 300 kg. |
| `Spacetime.tsx` | Shahd | `state` | The wow visual — see section 3. |
| `Receipts.tsx` | Narimane | `state` | For each `state.receipts[i]`: "TRUE TIE" label (violet), `explanation`, policy, `seed` (first 12 chars, mono), `order`, `allocation`. Empty: "No true tie yet. Book from Earth and Mars within one light delay." |
| `PolicyPicker.tsx` | Narimane | `state`, `date`, `onDateChange`, `onChanged` | Radio: lottery / prorata / priority. Date input. Capacity input (default 500). **Apply** → `api.scenario({date, compression: 60, resource: {...state.resource, capacity}, policy})` then `onChanged(newState)` and `onDateChange(date)`. **Reset** → `api.reset()` then `onChanged(newState)`. Show a note that Apply clears current bookings. |
| `FairnessLab.tsx` | Narimane | `date` | Button "Run 10,000 races" → `api.fairness(date)`. Show 3 horizontal bars (SVG or divs with width %): Mars win rate with Earth server / Mars server / Lightcone, plus tie rate. Caption: "Simulation: one Earth and one Mars request at random times within 30 min, real light delay for {date}." |
| `App.tsx` | Shahd | — | Already done. Shahd may adjust layout/styling. The "Naive vs Lightcone" tab is already in it. |

**Git rule:** only edit the files you own. Pull before you start, push every hour.

## 3. The spacetime diagram (Shahd) — exact math

SVG, for example `width = 100%`, `viewBox="0 0 600 H"`, with `H = 560`.

- **Earth line:** vertical at `x = 100`. **Mars line:** vertical at `x = 500`. Labels "EARTH" (earth colour) and "MARS" (mars colour) at the top.
- **Time → y:** show a window of time ending at "now". Let
  `span = max(4 * state.one_way_s, 600)` seconds,
  `t0 = max(0, state.sim_t - span)`,
  `y(t) = 40 + (t - t0) / span * (H - 60)`.
  So time goes **down**, and "now" is near the bottom.
- **"Now" line:** horizontal dashed line at `y(state.sim_t)`, label with the time in hh:mm:ss.
- **Requests (dots):** take all requests from `state.nodes.earth.log` and `state.nodes.mars.log`, deduplicated by `id`. Each dot at `x = 100` (earth) or `500` (mars), `y = y(r.sim_t)`, radius 7.
  - `status === "provisional"` → dashed stroke, no fill.
  - `status === "final"` → solid `final` green fill.
  - `status === "frozen"` → amber stroke.
  - Label next to the dot: `r.id · r.qty kg`.
- **Light signals (gold lines):** for each `m` in `state.in_flight`:
  - start: `(x(m.from_node), y(m.sent_t))`
  - end: `(x(m.to_node), y(m.arrive_t))`
  - if `m.delivered` is false, the signal is still travelling: cut the line at the current time. Fraction `f = (state.sim_t - m.sent_t) / (m.arrive_t - m.sent_t)` (clamp 0–1), and the end point becomes `start + f * (end - start)`. Draw it in `signal` gold; delivered lines a bit more transparent.
- **True ties:** collect every id in `state.receipts[*].tie`. Those dots get a violet (`tie`) glow (a larger circle behind, opacity 0.3) and a "TRUE TIE" label between the two lines at the average y of the tied requests.
- Animation is optional: the 500 ms polling already makes the gold lines move. If Framer Motion causes trouble, skip it.

Why this visual works for the jury: a tie is visible as **two dots with no gold line connecting them in time** — the news from one hadn't reached the other when it acted.

## 4. Useful helpers

```ts
export const fmt = (s: number) => {
  const t = Math.round(s)
  const h = String(Math.floor(t / 3600)).padStart(2, '0')
  const m = String(Math.floor((t % 3600) / 60)).padStart(2, '0')
  const sec = String(t % 60).padStart(2, '0')
  return `${h}:${m}:${sec}`
}
```
Use it in LinkBar, Spacetime and Receipts (each person can paste it into their own file to avoid shared-file conflicts).

## 5. Tailwind classes you can use

Colours: `bg-ink`, `bg-panel`, `border-line`, `text-text`, `text-muted`, `text-earth`, `text-mars`, `text-signal`, `text-tie`, `text-final` (also `bg-…`, `border-…`, `fill-…`, `stroke-…`). Fonts: `font-sans` (Inter), `font-mono` (JetBrains Mono — use for numbers, times, hashes). In SVG you can also write colours directly: `#4EA8FF` earth, `#E0603A` mars, `#F5D27A` gold, `#B79CFF` violet, `#3FB950` green, `#8B93A7` muted, `#252A35` lines.

## 6. Test checklist before 06:00 freeze

- Book Earth, then Mars before the gold line arrives → after the signals arrive, TRUE TIE appears on the diagram and in Receipts.
- Book Mars after the Earth signal has arrived → no tie; Earth served first.
- After one round trip, dots turn green and Earth/Mars hashes match.
- Policy → prorata → Apply → book again → shares are proportional.
- Fairness Lab shows three bars.
- Stop the backend → error banner appears; restart → it recovers.
- Pick a conjunction date → amber link bar, requests show "frozen".
