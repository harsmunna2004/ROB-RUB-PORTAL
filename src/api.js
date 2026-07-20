async function request(url, options) {
  const response = await fetch(url, options)
  const data = await response.json()
  if (!response.ok) throw new Error(data.detail || 'Something went wrong. Please try again.')
  return data
}

export const api = {
  getRos: () => request('/api/ros'),
  getPius: (ro) => request(`/api/pius?ro=${encodeURIComponent(ro)}`),
  getProjects: (ro, piu) => request(`/api/projects?ro=${encodeURIComponent(ro)}&piu=${encodeURIComponent(piu)}`),
  createMappings: (upc, proposalIds) => request('/api/mappings', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ upc, proposal_ids: proposalIds }),
  }),
}
