import { NavLink, Outlet } from 'react-router-dom'

export default function AppShell() {
  return <><header className="site-header"><div className="header-inner"><div><span className="eyebrow">NHAI ASSET MAPPING</span><strong>ROB/RUB Portal</strong></div><nav>
    <NavLink to="/projects">Projects</NavLink><NavLink to="/rob-rubs">ROB/RUB Database</NavLink><NavLink to="/dashboard">Dashboard</NavLink>
  </nav></div></header><main className="page-shell"><Outlet /></main></>
}
