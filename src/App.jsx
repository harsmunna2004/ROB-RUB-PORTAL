import { useEffect, useState } from 'react'
import { api } from './api'

const emptyRow = () => ({ id: crypto.randomUUID(), value: '' })

export default function App() {
  const [ros, setRos] = useState([])
  const [pius, setPius] = useState([])
  const [projects, setProjects] = useState([])
  const [ro, setRo] = useState('')
  const [piu, setPiu] = useState('')
  const [upc, setUpc] = useState('')
  const [rows, setRows] = useState([emptyRow()])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [results, setResults] = useState([])

  useEffect(() => {
    api.getRos().then(setRos).catch((err) => setError(err.message))
  }, [])

  async function handleRoChange(event) {
    const selectedRo = event.target.value
    setRo(selectedRo)
    setPiu('')
    setUpc('')
    setPius([])
    setProjects([])
    setResults([])
    setError('')
    if (selectedRo) {
      try { setPius(await api.getPius(selectedRo)) }
      catch (err) { setError(err.message) }
    }
  }

  async function handlePiuChange(event) {
    const selectedPiu = event.target.value
    setPiu(selectedPiu)
    setUpc('')
    setProjects([])
    setResults([])
    setError('')
    if (selectedPiu) {
      try { setProjects(await api.getProjects(ro, selectedPiu)) }
      catch (err) { setError(err.message) }
    }
  }

  function updateRow(id, value) {
    setRows((current) => current.map((row) => row.id === id ? { ...row, value } : row))
  }

  function removeRow(id) {
    setRows((current) => current.filter((row) => row.id !== id))
  }

  async function handleSubmit(event) {
    event.preventDefault()
    setError('')
    setResults([])
    const proposalIds = rows.map((row) => row.value.trim()).filter(Boolean)
    if (!ro || !piu || !upc) return setError('Select an RO, PIU, and project.')
    if (!proposalIds.length) return setError('Enter at least one ROB/RUB ID.')
    if (new Set(proposalIds).size !== proposalIds.length) return setError('Enter each ROB/RUB ID only once.')

    setLoading(true)
    try {
      const response = await api.createMappings(upc, proposalIds)
      setResults(response.results)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="page-shell">
      <section className="hero">
        <p className="eyebrow">NHAI ASSET MAPPING</p>
        <h1>ROB/RUB Mapping Portal</h1>
        <p>Select the organizational hierarchy and map one or more ROB/RUB proposal IDs to a project.</p>
      </section>

      <form className="mapping-card" onSubmit={handleSubmit}>
        <div className="step-title"><span>1</span><div><h2>Select project</h2><p>Options are loaded from your Supabase projects table.</p></div></div>
        <div className="select-grid">
          <label>Regional Office (RO)
            <select value={ro} onChange={handleRoChange}>
              <option value="">Select an RO</option>
              {ros.map((item) => <option key={item}>{item}</option>)}
            </select>
          </label>
          <label>Project Implementation Unit (PIU)
            <select value={piu} onChange={handlePiuChange} disabled={!ro}>
              <option value="">Select a PIU</option>
              {pius.map((item) => <option key={item}>{item}</option>)}
            </select>
          </label>
          <label className="project-field">Project
            <select value={upc} onChange={(event) => { setUpc(event.target.value); setResults([]) }} disabled={!piu}>
              <option value="">Select a project</option>
              {projects.map((project) => <option key={project.upc} value={project.upc}>{project.project_name} ({project.upc})</option>)}
            </select>
          </label>
        </div>

        <div className="divider" />
        <div className="step-title"><span>2</span><div><h2>Add ROB/RUB IDs</h2><p>A project can contain multiple ROB/RUB records.</p></div></div>
        <div className="id-list">
          {rows.map((row, index) => (
            <div className="id-row" key={row.id}>
              <label>ROB/RUB Proposal ID {index + 1}
                <input value={row.value} onChange={(event) => updateRow(row.id, event.target.value)} placeholder="Example: ROB-001" />
              </label>
              {rows.length > 1 && <button type="button" className="remove-button" aria-label={`Remove ROB/RUB row ${index + 1}`} onClick={() => removeRow(row.id)}>Remove</button>}
            </div>
          ))}
        </div>
        <button type="button" className="add-button" onClick={() => setRows((current) => [...current, emptyRow()])}>+ Add another ROB/RUB</button>

        {error && <div className="alert error" role="alert">{error}</div>}
        {results.length > 0 && <div className="results" aria-live="polite">
          <h3>Mapping results</h3>
          {results.map((result, index) => <div className={`result ${result.status}`} key={`${result.proposal_id}-${index}`}><strong>{result.proposal_id || 'Blank ID'}</strong><span>{result.message}</span></div>)}
        </div>}

        <button className="submit-button" type="submit" disabled={loading}>{loading ? 'Saving…' : 'Save mappings'}</button>
      </form>
    </main>
  )
}
