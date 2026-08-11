import { useState } from 'react'

import { apiErrorMessage } from '@/lib/errors'

/** Shared open / pending / error state for a dialog-backed form or confirmation. */
export function useDialogForm() {
  const [open, setOpen] = useState(false)
  const [pending, setPending] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function run(action: () => Promise<unknown>) {
    setError(null)
    setPending(true)
    try {
      await action()
      setOpen(false)
    } catch (caught) {
      setError(apiErrorMessage(caught))
    } finally {
      setPending(false)
    }
  }

  return { open, setOpen, pending, error, run }
}
