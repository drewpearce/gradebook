import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import { ConfirmDialog } from './ConfirmDialog'

async function setup() {
  const onConfirm = vi.fn().mockResolvedValue(undefined)
  render(
    <ConfirmDialog
      trigger={<button>Open</button>}
      title="Delete class?"
      description="Remove it."
      confirmText="Room 5"
      onConfirm={onConfirm}
    />,
  )
  await userEvent.click(screen.getByText('Open'))
  return { onConfirm }
}

const deleteButton = () => screen.getByRole('button', { name: 'Delete' })
const input = () => screen.getByLabelText('Type “Room 5” to confirm')

describe('ConfirmDialog confirmText', () => {
  it('keeps Delete disabled until the exact name is typed, then confirms once', async () => {
    const { onConfirm } = await setup()
    expect(deleteButton()).toBeDisabled()

    await userEvent.type(input(), 'Room 6')
    expect(deleteButton()).toBeDisabled()

    await userEvent.clear(input())
    await userEvent.type(input(), '  Room 5  ')
    expect(deleteButton()).toBeEnabled()

    await userEvent.click(deleteButton())
    expect(onConfirm).toHaveBeenCalledTimes(1)
  })

  it('clears the typed name when the dialog is reopened', async () => {
    await setup()
    await userEvent.type(input(), 'Room 5')
    await userEvent.click(screen.getByRole('button', { name: 'Cancel' }))
    await userEvent.click(screen.getByText('Open'))
    expect(input()).toHaveValue('')
    expect(deleteButton()).toBeDisabled()
  })
})
