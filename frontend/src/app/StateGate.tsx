import type { ReactNode } from 'react'
import { useLightcone } from '../context/LightconeContext'
import type { StateOut } from '../types'

/** Garde : évite de répéter « Loading… » dans chaque page. */
export default function StateGate({ children }: { children: (state: StateOut) => ReactNode }) {
  const { state } = useLightcone()
  return state ? <>{children(state)}</> : <p className="text-muted">Loading…</p>
}
