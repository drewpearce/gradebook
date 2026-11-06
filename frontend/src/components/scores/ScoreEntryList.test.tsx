import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import { ScoreRow } from './ScoreEntryList'

function setup(overrides: Partial<Parameters<typeof ScoreRow>[0]> = {}) {
  const onSave = vi.fn().mockResolvedValue(undefined)
  const onClear = vi.fn().mockResolvedValue(undefined)
  render(
    <ul>
      <ScoreRow
        label="Ada"
        persisted={undefined}
        maxPoints="10.00"
        onSave={onSave}
        onClear={onClear}
        {...overrides}
      />
    </ul>,
  )
  return { onSave, onClear, input: screen.getByLabelText('Ada score') }
}

describe('ScoreRow', () => {
  it('saves a typed value on blur', async () => {
    const { onSave, input } = setup()
    await userEvent.type(input, '7.5')
    await userEvent.tab()
    expect(onSave).toHaveBeenCalledWith('7.5')
  })

  it('saves "0" as a score instead of clearing', async () => {
    const { onSave, onClear, input } = setup()
    await userEvent.type(input, '0')
    await userEvent.tab()
    expect(onSave).toHaveBeenCalledWith('0')
    expect(onClear).not.toHaveBeenCalled()
  })

  it('shows a persisted 0 as 0, not blank', () => {
    const { input } = setup({ persisted: '0.00' })
    expect(input).toHaveValue('0')
  })

  it('clears a persisted score when the input is emptied', async () => {
    const { onSave, onClear, input } = setup({ persisted: '8.00' })
    await userEvent.clear(input)
    await userEvent.tab()
    expect(onClear).toHaveBeenCalledTimes(1)
    expect(onSave).not.toHaveBeenCalled()
  })

  it('does not call onClear when an empty input was never scored', async () => {
    const { onClear, input } = setup()
    await userEvent.click(input)
    await userEvent.tab()
    expect(onClear).not.toHaveBeenCalled()
  })

  it.each(['0x10', '1e3', '8.555', '-1', 'abc'])('rejects "%s" locally', async (text) => {
    const { onSave, input } = setup()
    await userEvent.type(input, text)
    await userEvent.tab()
    expect(onSave).not.toHaveBeenCalled()
    expect(screen.getByText('Enter a number ≥ 0 with at most 2 decimals')).toBeVisible()
    expect(input).toHaveAttribute('aria-invalid', 'true')
  })

  it('shows "Not saved. Try again." and keeps the typed text when the save fails', async () => {
    const { input } = setup({ onSave: vi.fn().mockRejectedValue(new Error('500')) })
    await userEvent.type(input, '7')
    await userEvent.tab()
    expect(await screen.findByText('Not saved. Try again.')).toBeVisible()
    expect(input).toHaveValue('7')
  })

  it('shows the same error when a clear fails', async () => {
    const { input } = setup({
      persisted: '8.00',
      onClear: vi.fn().mockRejectedValue(new Error('500')),
    })
    await userEvent.clear(input)
    await userEvent.tab()
    expect(await screen.findByText('Not saved. Try again.')).toBeVisible()
  })

  it('clears the error after a later successful save', async () => {
    const onSave = vi
      .fn()
      .mockRejectedValueOnce(new Error('500'))
      .mockResolvedValue(undefined)
    const { input } = setup({ onSave })
    await userEvent.type(input, '7')
    await userEvent.tab()
    await screen.findByText('Not saved. Try again.')
    await userEvent.click(input)
    await userEvent.tab()
    expect(onSave).toHaveBeenCalledTimes(2)
    expect(screen.queryByText('Not saved. Try again.')).not.toBeInTheDocument()
  })

  it('points aria-describedby at the error text', async () => {
    const { input } = setup()
    await userEvent.type(input, 'abc')
    await userEvent.tab()
    const id = input.getAttribute('aria-describedby')
    expect(id).toBeTruthy()
    expect(document.getElementById(id!)).toHaveTextContent(/Enter a number/)
  })

  it('shows a non-blocking hint above the max and still saves', async () => {
    const { onSave, input } = setup()
    await userEvent.type(input, '12')
    expect(screen.getByText('Above max (10)')).toBeVisible()
    await userEvent.tab()
    expect(onSave).toHaveBeenCalledWith('12')
  })

  it('disables the input while scores are loading', () => {
    const { input } = setup({ disabled: true })
    expect(input).toBeDisabled()
  })

  it('moves focus to the next row score input on Enter', async () => {
    const onSave = vi.fn().mockResolvedValue(undefined)
    render(
      <ul>
        {['Ada', 'Bo'].map((name) => (
          <ScoreRow
            key={name}
            label={name}
            persisted={undefined}
            maxPoints="10"
            onSave={onSave}
            onClear={vi.fn()}
          />
        ))}
      </ul>,
    )
    await userEvent.type(screen.getByLabelText('Ada score'), '5{Enter}')
    expect(screen.getByLabelText('Bo score')).toHaveFocus()
    expect(onSave).toHaveBeenCalledWith('5')
  })

  it('keeps what the teacher is typing when the persisted value changes under focus', async () => {
    const props = { label: 'Ada', maxPoints: '10', onSave: vi.fn(), onClear: vi.fn() }
    const { rerender } = render(
      <ul>
        <ScoreRow {...props} persisted="3.00" />
      </ul>,
    )
    const input = screen.getByLabelText('Ada score')
    await userEvent.clear(input)
    await userEvent.type(input, '9')
    rerender(
      <ul>
        <ScoreRow {...props} persisted="4.00" />
      </ul>,
    )
    expect(input).toHaveValue('9')
  })
})
