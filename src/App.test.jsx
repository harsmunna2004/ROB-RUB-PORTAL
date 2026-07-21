import { cleanup, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import App from './App'

const response = (data) => Promise.resolve({ ok: true, json: () => Promise.resolve(data) })

describe('certification portal', () => {
  beforeEach(() => {
    history.pushState({}, '', '/')
    global.fetch = vi.fn((url, options) => {
      if (url === '/api/ros') return response(['Delhi'])
      if (url.includes('/api/pius')) return response(['Dwarka'])
      if (url.startsWith('/api/projects?')) return response([{ ro: 'Delhi', piu: 'Dwarka', project_name: 'NH-48 Package', upc: 'UPC-001', certification_status: 'pending', certified_at: null, mapped_rob_rub_count: 0 }])
      if (url === '/api/projects?upc=UPC-001' && !options) return response({ ro: 'Delhi', piu: 'Dwarka', project_name: 'NH-48 Package', upc: 'UPC-001', certification_status: 'pending', certified_at: null, mapped_rob_rub_count: 0, mappings: [] })
      if (url === '/api/projects?upc=UPC-001' && options?.method === 'PATCH') return response({ ro: 'Delhi', piu: 'Dwarka', project_name: 'NH-48 Package', upc: 'UPC-001', certification_status: 'certified', certified_at: '2026-07-21T00:00:00Z', mapped_rob_rub_count: 0, mappings: [] })
      throw new Error(`Unexpected request: ${url}`)
    })
    vi.spyOn(window, 'confirm').mockReturnValue(true)
  })
  afterEach(() => { cleanup(); vi.restoreAllMocks() })

  it('shows project grid and opens certification workflow', async () => {
    const user = userEvent.setup(); render(<App />)
    await user.selectOptions(await screen.findByLabelText('Regional Office (RO)'), 'Delhi')
    await user.selectOptions(await screen.findByLabelText('Project Implementation Unit (PIU)'), 'Dwarka')
    expect(await screen.findByText('UPC-001')).toBeInTheDocument()
    await user.click(screen.getByRole('link', { name: 'Manage' }))
    expect(await screen.findByText('Are there any ROBs/RUBs in this project?')).toBeInTheDocument()
  })

  it('certifies a project with no mappings', async () => {
    history.pushState({}, '', '/projects/UPC-001/certify')
    const user = userEvent.setup(); render(<App />)
    await user.click(await screen.findByRole('button', { name: 'No ROBs/RUBs' }))
    await user.click(screen.getByRole('button', { name: 'Certify project' }))
    expect(await screen.findByText('Project certified successfully.')).toBeInTheDocument()
  })
})
