import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from 'react'
import { api } from '../api'
import { mockState } from '../mock/state'
import { usePolling } from '../hooks/usePolling'
import type { LinkInfo, StateOut } from '../types'

const USE_MOCK = false
const DEFAULT_DATE = '2040-01-01'

interface LightconeCtx {
  state: StateOut | null
  link: LinkInfo | null
  date: string
  error: string | null
  setDate: (d: string) => void
  setState: (s: StateOut) => void
  refresh: () => Promise<void>
}

const Ctx = createContext<LightconeCtx | null>(null)

/** Source unique de vérité : un seul polling pour toutes les pages. */
export function LightconeProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<StateOut | null>(USE_MOCK ? mockState : null)
  const [link, setLink] = useState<LinkInfo | null>(null)
  const [date, setDate] = useState(DEFAULT_DATE)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (USE_MOCK) return
    api.link(date).then(setLink).catch((e) => setError(String(e)))
  }, [date])

  const refresh = useCallback(
    () =>
      api
        .state()
        .then((s) => {
          setState(s)
          setError(null)
        })
        .catch((e) => setError(String(e))),
    [],
  )

  usePolling(refresh, 500, !USE_MOCK)

  const value = useMemo(
    () => ({ state, link, date, error, setDate, setState, refresh }),
    [state, link, date, error, refresh],
  )
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>
}

export function useLightcone() {
  const ctx = useContext(Ctx)
  if (!ctx) throw new Error('useLightcone must be used inside <LightconeProvider>')
  return ctx
}
