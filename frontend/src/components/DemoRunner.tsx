import { useState } from 'react'
import { api } from '../api'
import type { StateOut } from '../types'

interface Props {
  state: StateOut | null
  onChanged: (state: StateOut) => void
}

const wait = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms))

export const bookEvent = (node: 'earth' | 'mars') => `lightcone-book-${node}`

export default function DemoRunner({ state, onChanged }: Props) {
  const [step, setStep] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  const gapMs = state ? Math.min(1500, Math.max(400, (state.one_way_s * 1000) / state.compression / 4)) : 1200

  const run = async () => {
    setError(null)
    try {
      setStep('Resetting both nodes…')
      onChanged(await api.reset())
      await wait(400)
      setStep('Earth books…')
      window.dispatchEvent(new Event(bookEvent('earth')))
      await wait(gapMs)
      setStep(`Mars books ${(gapMs / 1000).toFixed(1)} s later, before Earth's news can arrive…`)
      window.dispatchEvent(new Event(bookEvent('mars')))
      await wait(800)
      setStep('Signals in flight. Watch the TRUE TIE appear when the news arrives.')
      await wait(4000)
      setStep(null)
    } catch (e) {
      setError(String(e))
      setStep(null)
    }
  }

  return (
    <div className="flex flex-wrap items-center gap-3">
      <button
        onClick={run}
        disabled={step !== null || !state}
        className="rounded bg-tie px-4 py-2 text-sm font-semibold text-ink disabled:opacity-50"
      >
        {step ? 'Running…' : 'Run true-tie demo'}
      </button>
      <span className="text-sm text-muted">
        {step ?? 'Resets, then books Earth and Mars with the mandates shown in each panel, within one light delay.'}
      </span>
      {error && <span className="text-sm text-mars">{error}</span>}
    </div>
  )
}
