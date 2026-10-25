import { lazy, type ComponentType, type LazyExoticComponent } from 'react'

export interface AppRoute {
  path: string // '' = index
  label: string
  description: string
  Page: LazyExoticComponent<ComponentType>
}

/**
 * Registre de routes (data-driven) : la Sidebar, le routeur et les cartes du
 * Dashboard sont tous générés ici. Ajouter une page = ajouter une ligne.
 */
export const DASHBOARD: AppRoute = {
  path: '',
  label: 'Dashboard',
  description: 'Vue d’ensemble du scénario',
  Page: lazy(() => import('../pages/DashboardPage')),
}

export const SECTIONS: AppRoute[] = [
  { path: 'simulation', label: 'Simulation', description: 'Réserver depuis la Terre et Mars, diagramme espace-temps', Page: lazy(() => import('../pages/SimulationPage')) },
  { path: 'receipts', label: 'Receipts', description: 'Reçus vérifiables des vraies égalités', Page: lazy(() => import('../pages/ReceiptsPage')) },
  { path: 'policy', label: 'Policy', description: 'Règle d’équité, date et capacité', Page: lazy(() => import('../pages/PolicyPage')) },
  { path: 'fairness', label: 'Fairness Lab', description: 'Monte Carlo : 10 000 courses simulées', Page: lazy(() => import('../pages/FairnessPage')) },
  { path: 'comparison', label: 'Naive vs Lightcone', description: 'Serveur central sur Terre contre Lightcone', Page: lazy(() => import('../pages/ComparisonPage')) },
]
