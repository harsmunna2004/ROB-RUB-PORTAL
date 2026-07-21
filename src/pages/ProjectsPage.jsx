import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api'
import Breadcrumbs from '../components/Breadcrumbs'
import SearchableSelect from '../components/SearchableSelect'
import StatusBadge from '../components/StatusBadge'

const CACHE_KEY='rob-rub-project-hierarchy-v1'
function cachedProjects(){try{return JSON.parse(sessionStorage.getItem(CACHE_KEY)||'[]')}catch{return []}}
const unique=values=>[...new Set(values.filter(Boolean))].sort((a,b)=>a.localeCompare(b))

export default function ProjectsPage(){
  const [allProjects,setAllProjects]=useState(cachedProjects),[ro,setRo]=useState(''),[piu,setPiu]=useState(''),[error,setError]=useState(''),[loading,setLoading]=useState(!cachedProjects().length)
  useEffect(()=>{let active=true;api.getProjectHierarchy().then(data=>{if(!active)return;setAllProjects(data.projects);sessionStorage.setItem(CACHE_KEY,JSON.stringify(data.projects));setError('')}).catch(e=>{if(active)setError(e.message)}).finally(()=>{if(active)setLoading(false)});return()=>{active=false}},[])
  const ros=useMemo(()=>unique(allProjects.map(project=>project.ro)),[allProjects])
  const pius=useMemo(()=>unique(allProjects.filter(project=>project.ro===ro).map(project=>project.piu)),[allProjects,ro])
  const projects=useMemo(()=>allProjects.filter(project=>project.ro===ro&&project.piu===piu),[allProjects,ro,piu])
  function changeRo(value){setRo(value);setPiu('')}
  return <><Breadcrumbs items={[{label:'Projects'}]}/><section className="page-heading"><h1>Project certification</h1><p>Select an RO and PIU to certify every project.</p></section><section className="card"><div className="filters two"><SearchableSelect label="Regional Office (RO)" value={ro} options={ros} onChange={changeRo} placeholder="Select an RO" loading={loading}/><SearchableSelect label="Project Implementation Unit (PIU)" value={piu} options={pius} onChange={setPiu} placeholder="Select a PIU" disabled={!ro} loading={loading&&!!ro}/></div>{error&&<div className="alert error">{error}</div>}{piu&&<div className="table-scroll"><table><thead><tr><th>UPC</th><th>Project Name</th><th>Certification Status</th><th>ROBs/RUBs Mapped</th><th>Action</th></tr></thead><tbody>{projects.map(project=><tr key={project.upc}><td>{project.upc}</td><td>{project.project_name}</td><td><StatusBadge status={project.certification_status}/></td><td>{project.mapped_rob_rub_count}</td><td><Link className="button small" to={`/projects/${encodeURIComponent(project.upc)}/certify`}>{project.certification_status==='certified'?'View':'Manage'}</Link></td></tr>)}</tbody></table>{projects.length===0&&<p className="empty">No projects found for this PIU.</p>}</div>}</section></>
}
