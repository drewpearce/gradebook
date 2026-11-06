import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import { QueryState } from './QueryState'

const ok = { isPending: false, isError: false, refetch: vi.fn() }

describe('QueryState', () => {
  it('shows Loading… and not the children while a query is pending', () => {
    render(
      <QueryState queries={[ok, { ...ok, isPending: true }]}>
        <p>Empty text</p>
      </QueryState>,
    )
    expect(screen.getByText('Loading…')).toBeInTheDocument()
    expect(screen.queryByText('Empty text')).not.toBeInTheDocument()
  })

  it('shows an error and retries the failed query', async () => {
    const refetch = vi.fn()
    render(
      <QueryState queries={[ok, { isPending: false, isError: true, refetch }]}>
        <p>Empty text</p>
      </QueryState>,
    )
    expect(screen.queryByText('Empty text')).not.toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: 'Retry' }))
    expect(refetch).toHaveBeenCalledTimes(1)
  })

  it('shows the children once every query has loaded', () => {
    render(
      <QueryState queries={[ok]}>
        <p>Empty text</p>
      </QueryState>,
    )
    expect(screen.getByText('Empty text')).toBeInTheDocument()
  })
})
