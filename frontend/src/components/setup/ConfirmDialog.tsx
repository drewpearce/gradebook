import { useState, type ReactNode } from 'react'

import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { useDialogForm } from '@/components/setup/useDialogForm'

export function ConfirmDialog({
  trigger,
  title,
  description,
  details,
  confirmText,
  onConfirm,
}: {
  trigger: ReactNode
  title: string
  description: string
  /** Extra content under the description, e.g. what else the delete removes. */
  details?: ReactNode
  /** If set, Delete stays disabled until the user types this (ignoring outer spaces). */
  confirmText?: string
  onConfirm: () => Promise<unknown>
}) {
  const { open, setOpen, pending, error, run } = useDialogForm()
  const [typed, setTyped] = useState('')
  const blocked = confirmText !== undefined && typed.trim() !== confirmText.trim()

  return (
    <Dialog
      open={open}
      onOpenChange={(next) => {
        setTyped('')
        setOpen(next)
      }}
    >
      <DialogTrigger asChild>{trigger}</DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{title}</DialogTitle>
          <DialogDescription>{description}</DialogDescription>
        </DialogHeader>
        {details}
        {confirmText !== undefined ? (
          <div className="grid gap-2">
            <Label htmlFor="confirm-text">Type “{confirmText}” to confirm</Label>
            <Input
              id="confirm-text"
              value={typed}
              onChange={(event) => setTyped(event.target.value)}
              autoComplete="off"
            />
          </div>
        ) : null}
        {error ? <p className="text-sm text-destructive">{error}</p> : null}
        <DialogFooter>
          <Button variant="outline" onClick={() => setOpen(false)} disabled={pending}>
            Cancel
          </Button>
          <Button
            variant="destructive"
            onClick={() => void run(onConfirm)}
            disabled={pending || blocked}
          >
            {pending ? 'Working…' : 'Delete'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
