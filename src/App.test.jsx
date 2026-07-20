import { cleanup, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import App from './App'

const jsonResponse = (data, ok = true) =>
  Promise.resolve({ ok, json: () => Promise.resolve(data) })

describe('ROB/RUB mapping form', () => {
  beforeEach(() => {
    global.fetch = vi.fn((url, options) => {
      if (url === '/api/ros') return jsonResponse(['Delhi', 'Mumbai'])
      if (url.includes('/api/pius')) return jsonResponse(['Dwarka'])
      if (url.includes('/api/projects')) {
        return jsonResponse([{ ro: 'Delhi', piu: 'Dwarka', project_name: 'NH-48 Package', upc: 'UPC-001' }])
      }
      if (url === '/api/mappings' && options?.method === 'POST') {
        return jsonResponse({ results: [
          { proposal_id: 'ROB-001', status: 'saved', message: 'Mapping saved successfully.' },
          { proposal_id: 'RUB-002', status: 'saved', message: 'Mapping saved successfully.' },
        ] })
      }
      throw new Error(`Unexpected request: ${url}`)
    })
  })

  afterEach(() => {
    cleanup()
    vi.restoreAllMocks()
  })

  it('loads dependent RO, PIU, and project dropdowns', async () => {
    const user = userEvent.setup()
    render(<App />)
    await user.selectOptions(await screen.findByLabelText('Regional Office (RO)'), 'Delhi')
    await user.selectOptions(await screen.findByLabelText('Project Implementation Unit (PIU)'), 'Dwarka')
    expect(await screen.findByRole('option', { name: 'NH-48 Package (UPC-001)' })).toBeInTheDocument()
  })

  it('adds and removes ROB/RUB input rows', async () => {
    const user = userEvent.setup()
    render(<App />)
    expect(screen.getAllByLabelText(/ROB\/RUB Proposal ID/)).toHaveLength(1)
    await user.click(screen.getByRole('button', { name: /Add another ROB\/RUB/ }))
    expect(screen.getAllByLabelText(/ROB\/RUB Proposal ID/)).toHaveLength(2)
    await user.click(screen.getByRole('button', { name: 'Remove ROB/RUB row 2' }))
    expect(screen.getAllByLabelText(/ROB\/RUB Proposal ID/)).toHaveLength(1)
  })

  it('blocks duplicate IDs entered in the same form', async () => {
    const user = userEvent.setup()
    render(<App />)
    await completeHierarchy(user)
    await user.type(screen.getByLabelText('ROB/RUB Proposal ID 1'), 'ROB-001')
    await user.click(screen.getByRole('button', { name: /Add another ROB\/RUB/ }))
    await user.type(screen.getByLabelText('ROB/RUB Proposal ID 2'), ' ROB-001 ')
    await user.click(screen.getByRole('button', { name: 'Save mappings' }))
    expect(await screen.findByText('Enter each ROB/RUB ID only once.')).toBeInTheDocument()
    expect(fetch).not.toHaveBeenCalledWith('/api/mappings', expect.anything())
  })

  it('submits multiple IDs for the selected project', async () => {
    const user = userEvent.setup()
    render(<App />)
    await completeHierarchy(user)
    await user.type(screen.getByLabelText('ROB/RUB Proposal ID 1'), 'ROB-001')
    await user.click(screen.getByRole('button', { name: /Add another ROB\/RUB/ }))
    await user.type(screen.getByLabelText('ROB/RUB Proposal ID 2'), 'RUB-002')
    await user.click(screen.getByRole('button', { name: 'Save mappings' }))

    await waitFor(() => expect(fetch).toHaveBeenCalledWith('/api/mappings', expect.objectContaining({
      method: 'POST',
      body: JSON.stringify({ upc: 'UPC-001', proposal_ids: ['ROB-001', 'RUB-002'] }),
    })))
    expect(await screen.findAllByText('Mapping saved successfully.')).toHaveLength(2)
  })
})

async function completeHierarchy(user) {
  await user.selectOptions(await screen.findByLabelText('Regional Office (RO)'), 'Delhi')
  await user.selectOptions(await screen.findByLabelText('Project Implementation Unit (PIU)'), 'Dwarka')
  await user.selectOptions(await screen.findByLabelText('Project'), 'UPC-001')
}
