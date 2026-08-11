import { useEffect, useState, type FormEvent, type ReactNode } from 'react'

import { useCreateClass, useUpdateClass } from '@/api/classes'
import type { components } from '@/api/schema'
import { FormDialog } from '@/components/setup/FormDialog'
import { useDialogForm } from '@/components/setup/useDialogForm'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'

type Class = components['schemas']['ClassRead']

export function ClassDialog({
  existing,
  trigger,
  onCreated,
}: {
  existing?: Class
  trigger: ReactNode
  onCreated?: (created: Class) => void
}) {
  const { open, setOpen, pending, error, run } = useDialogForm()
  const [name, setName] = useState('')
  const create = useCreateClass()
  const update = useUpdateClass(existing?.id ?? '')

  useEffect(() => {
    if (open) {
      setName(existing?.name ?? '')
    }
  }, [open, existing])

  function handleSubmit(event: FormEvent) {
    event.preventDefault()
    void run(async () => {
      if (existing) {
        await update.mutateAsync({ name })
      } else {
        onCreated?.(await create.mutateAsync({ name }))
      }
    })
  }

  return (
    <FormDialog
      open={open}
      onOpenChange={setOpen}
      trigger={trigger}
      title={existing ? 'Rename class' : 'New class'}
      pending={pending}
      submitDisabled={name.trim() === ''}
      error={error}
      onSubmit={handleSubmit}
    >
      <div className="grid gap-2">
        <Label htmlFor="class-name">Name</Label>
        <Input
          id="class-name"
          value={name}
          onChange={(event) => setName(event.target.value)}
          placeholder="Room 1 (1st/2nd)"
          autoFocus
        />
      </div>
    </FormDialog>
  )
}
