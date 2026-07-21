import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import AppShell from './components/AppShell'
import CertificationPage from './pages/CertificationPage'
import DashboardPage from './pages/DashboardPage'
import ProjectsPage from './pages/ProjectsPage'
import RobRubDatabasePage from './pages/RobRubDatabasePage'

export default function App() {
  return <BrowserRouter><Routes><Route element={<AppShell />}>
    <Route index element={<Navigate to="/projects" replace />} />
    <Route path="/projects" element={<ProjectsPage />} />
    <Route path="/projects/:upc/certify" element={<CertificationPage />} />
    <Route path="/rob-rubs" element={<RobRubDatabasePage />} />
    <Route path="/dashboard" element={<DashboardPage />} />
  </Route></Routes></BrowserRouter>
}
