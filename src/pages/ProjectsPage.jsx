import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api'
import Breadcrumbs from '../components/Breadcrumbs'
import StatusBadge from '../components/StatusBadge'

export default function ProjectsPage() {
  const [ros, setRos] = useState([]), [pius, setPius] = useState([]), [projects, setProjects] = useState([])
  const [ro, setRo] = useState(''), [piu, setPiu] = useState(''), [error, setError] = useState('')
  useEffect(() => { api.getRos().then(setRos).catch(e => setError(e.message)) }, [])
  async function changeRo(e) { const value=e.target.value; setRo(value); setPiu(''); setProjects([]); setPius(value ? await api.getPius(value) : []) }
  async function changePiu(e) { const value=e.target.value; setPiu(value); setProjects(value ? await api.getProjects(ro, value) : []) }
  return <><Breadcrumbs items={[{label:'Projects'}]} /><section className="page-heading"><h1>Project certification</h1><p>Select an RO and PIU to certify every project.</p></section><section className="card">
    <div className="filters two"><label>Regional Office (RO)<select value={ro} onChange={changeRo}><option value="">Select an RO</option>{ros.map(x=><option key={x}>{x}</option>)}</select></label><label>Project Implementation Unit (PIU)<select value={piu} onChange={changePiu} disabled={!ro}><option value="">Select a PIU</option>{pius.map(x=><option key={x}>{x}</option>)}</select></label></div>
    {error && <div className="alert error">{error}</div>}{piu && <div className="table-scroll"><table><thead><tr><th>UPC</th><th>Project Name</th><th>Certification Status</th><th>ROBs/RUBs Mapped</th><th>Action</th></tr></thead><tbody>{projects.map(p=><tr key={p.upc}><td>{p.upc}</td><td>{p.project_name}</td><td><StatusBadge status={p.certification_status}/></td><td>{p.mapped_rob_rub_count}</td><td><Link className="button small" to={`/projects/${encodeURIComponent(p.upc)}/certify`}>{p.certification_status==='certified'?'View':'Manage'}</Link></td></tr>)}</tbody></table>{projects.length===0&&<p className="empty">No projects found for this PIU.</p>}</div>}
  </section></>
}
