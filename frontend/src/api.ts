import type { FairnessOut, LinkInfo, RequestIn, RequestOut, ScenarioIn, StateOut } from './types'

async function call<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`/api${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...init,
  })
  if (!res.ok) throw new Error(`${res.status} ${await res.text()}`)
  return res.json() as Promise<T>
}

export const api = {
  link: (date?: string) => call<LinkInfo>(`/link${date ? `?date=${date}` : ''}`),
  scenario: (body: ScenarioIn) => call<StateOut>('/scenario', { method: 'POST', body: JSON.stringify(body) }),
  request: (body: RequestIn) => call<RequestOut>('/request', { method: 'POST', body: JSON.stringify(body) }),
  state: () => call<StateOut>('/state'),
  reset: () => call<StateOut>('/reset', { method: 'POST' }),
  fairness: (date: string, trials = 10000) => call<FairnessOut>(`/fairness?date=${date}&trials=${trials}`),
}
