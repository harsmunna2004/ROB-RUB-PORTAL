import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { expect, it, vi } from 'vitest'
import SearchableSelect from './SearchableSelect'

it('opens a searchable option menu below the control and selects a value', async () => {
  const user = userEvent.setup()
  const onChange = vi.fn()
  render(<SearchableSelect label="Regional Office (RO)" value="" options={['Delhi', 'Mumbai']} onChange={onChange} placeholder="Select an RO" />)

  await user.click(screen.getByRole('button', { name: /regional office.*select an ro/i }))
  expect(screen.getByRole('listbox')).toHaveClass('select-menu')
  await user.type(screen.getByPlaceholderText('Search Regional Office (RO)'), 'del')
  expect(screen.getByRole('option', { name: 'Delhi' })).toBeVisible()
  expect(screen.queryByRole('option', { name: 'Mumbai' })).not.toBeInTheDocument()
  await user.click(screen.getByRole('option', { name: 'Delhi' }))
  expect(onChange).toHaveBeenCalledWith('Delhi')
  expect(screen.queryByRole('listbox')).not.toBeInTheDocument()
})
