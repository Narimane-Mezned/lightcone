import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { LightconeProvider } from './context/LightconeContext'
import AppShell from './app/AppShell'
import { DASHBOARD, SECTIONS } from './app/routes'

export default function App() {
  return (
    <LightconeProvider>
      <BrowserRouter>
        <Routes>
          <Route element={<AppShell />}>
            <Route index element={<DASHBOARD.Page />} />
            {SECTIONS.map(({ path, Page }) => (
              <Route key={path} path={path} element={<Page />} />
            ))}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </LightconeProvider>
  )
}
