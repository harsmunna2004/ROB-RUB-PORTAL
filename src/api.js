async function request(url, options) {
  const response = await fetch(url, options)
  const contentType = response.headers?.get?.('content-type') || ''
  const data = (contentType.includes('application/json') || typeof response.text !== 'function')
    ? await response.json()
    : { detail: await response.text() }
  if (!response.ok) throw new Error(data.detail || 'Something went wrong. Please try again.')
  return data
}

const query = (params) => new URLSearchParams(Object.entries(params).filter(([, value]) => value !== '' && value != null)).toString()

export const api = {
  getRos: () => request('/api/ros'),
  getPius: (ro) => request(`/api/pius?ro=${encodeURIComponent(ro)}`),
  getProjects: (ro, piu) => request(`/api/projects?${query({ ro, piu })}`),
  getProjectHierarchy: () => request('/api/projects?hierarchy=true'),
  getProject: (upc) => request(`/api/projects?${query({ upc })}`),
  setCertification: (upc, status) => request(`/api/projects?${query({ upc })}`, { method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ status }) }),
  createMappings: (upc, proposalIds) => request('/api/mappings', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ upc, proposal_ids: proposalIds }) }),
  deleteMapping: (upc, proposalId) => request(`/api/mappings?${query({ upc, proposal_id: proposalId })}`, { method: 'DELETE' }),
  getRobRubs: (params) => request(`/api/rob-rubs?${query(params)}`),
  getRobRubFilters: () => request('/api/rob-rubs/filters'),
  getDashboard: (params) => request(`/api/dashboard?${query(params)}`),
  dashboardCsvUrl: (params) => `/api/dashboard.csv?${query(params)}`,
}
