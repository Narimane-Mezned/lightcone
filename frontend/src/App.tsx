import { useEffect, useState } from 'react'
import { api } from './api'
import type { LinkInfo } from './types'

export default function App() {
  const [link, setLink] = useState<LinkInfo | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    api.link('2040-01-01').then(setLink).catch((e) => setError(String(e)))
  }, [])

  return (
    <main className="min-h-screen p-8">
      <h1 className="text-2xl font-semibold">Lightcone</h1>
      <p className="text-muted">Fair "first" for a multi-planet world.</p>
      {error && <p className="mt-4 text-mars">{error}</p>}
      {link && (
        <p className="mt-4 font-mono text-signal">
          Earth ⟷ Mars · {link.distance_au} AU · one-way {Math.round(link.one_way_s)} s
        </p>
      )}
    </main>
  )
}
