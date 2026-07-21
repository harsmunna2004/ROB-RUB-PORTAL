import { cleanup, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import App from './App'

const response = (data) => Promise.resolve({ ok: true, json: () => Promise.resolve(data) })

describe('certification portal', () => {
  beforeEach(() => {
    history.pushState({}, '', '/')
    sessionStorage.clear()
    global.fetch = vi.fn((url, options) => {
      if (url === '/api/projects?upc=UPC-001' && !options) return response({ ro: 'Delhi', piu: 'Dwarka', project_name: 'NH-48 Package', upc: 'UPC-001', certification_status: 'pending', certified_at: null, mapped_rob_rub_count: 0, mappings: [] })
      if (url === '/api/projects?upc=UPC-001' && options?.method === 'PATCH') return response({ ro: 'Delhi', piu: 'Dwarka', project_name: 'NH-48 Package', upc: 'UPC-001', certification_status: 'certified', certified_at: '2026-07-21T00:00:00Z', mapped_rob_rub_count: 0, mappings: [] })
      if (url === '/api/mappings' && options?.method === 'POST') return response({results:[{proposal_id:'ROB-001',status:'saved',message:'Mapping saved successfully.'}],saved_records:[{proposal_id:'ROB-001',proposal_date:'2026-01-15',name_of_work:'Delhi ROB',division_railway:'Northern Railway',state:'Delhi',associated_road_authority:'NHAI',category_of_road:'National Highway',name_of_road:'NH-48',date_mapped:'2026-07-21T00:00:00Z'}]})
      if (url === '/api/projects?hierarchy=true') return response({ projects: [{ ro: 'Delhi', piu: 'Dwarka', project_name: 'NH-48 Package', upc: 'UPC-001', certification_status: 'pending', certified_at: null, mapped_rob_rub_count: 0 }] })
      throw new Error(`Unexpected request: ${url}`)
    })
    vi.spyOn(window, 'confirm').mockReturnValue(true)
  })
  afterEach(() => { cleanup(); vi.restoreAllMocks() })

  it('shows project grid and opens certification workflow', async () => {
    const user = userEvent.setup(); render(<App />)
    await user.click(await screen.findByRole('button', {name:/regional office.*select an ro/i}))
    await user.click(screen.getByRole('option', {name:'Delhi'}))
    await user.click(screen.getByRole('button', {name:/project implementation unit.*select a piu/i}))
    await user.click(screen.getByRole('option', {name:'Dwarka'}))
    expect(await screen.findByText('UPC-001')).toBeInTheDocument()
    expect(global.fetch).toHaveBeenCalledWith('/api/projects?hierarchy=true', undefined)
    expect(global.fetch).toHaveBeenCalledTimes(1)
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

  it('shows complete mapping details immediately after saving without refetching', async () => {
    history.pushState({}, '', '/projects/UPC-001/certify')
    const user = userEvent.setup(); render(<App />)
    await user.click(await screen.findByRole('button', {name:'Yes, map ROBs/RUBs'}))
    await user.type(screen.getByLabelText('ROB/RUB Proposal ID 1'), 'ROB-001')
    await user.click(screen.getByRole('button', {name:'Save mappings'}))
    expect(await screen.findByRole('heading', {name:'Mapped ROBs/RUBs'})).toBeVisible()
    expect(screen.getByText('ROB-001')).toBeVisible()
    expect(screen.getByText('Delhi ROB')).toBeVisible()
    expect(screen.getByText('Northern Railway')).toBeVisible()
    expect(global.fetch.mock.calls.filter(([url])=>url==='/api/projects?upc=UPC-001')).toHaveLength(1)
  })
})
