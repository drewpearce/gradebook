import { useEffect, useState, type FormEvent, type ReactNode } from 'react'

import {
  useCreateGradeLevel,
  useDeleteGradeLevel,
  useGradeLevels,
  useUpdateGradeLevel,
} from '@/api/grade-levels'
import type { components } from '@/api/schema'
import { ConfirmDialog } from '@/components/setup/ConfirmDialog'
import { FormDialog } from '@/components/setup/FormDialog'
import { SetupSection } from '@/components/setup/SetupSection'
import { useDialogForm } from '@/components/setup/useDialogForm'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'

type GradeLevel = components['schemas']['GradeLevelRead']

function GradeLevelDialog({
  classId,
  gradeLevel,
  nextPosition,
  trigger,
}: {
  classId: string
  gradeLevel?: GradeLevel
  nextPosition?: number
  trigger: ReactNode
}) {
  const { open, setOpen, pending, error, run } = useDialogForm()
  const [name, setName] = useState('')
  const create = useCreateGradeLevel(classId)
  const update = useUpdateGradeLevel()

  useEffect(() => {
    if (open) {
      setName(gradeLevel?.name ?? '')
    }
  }, [open, gradeLevel])

  function handleSubmit(event: FormEvent) {
    event.preventDefault()
    void run(() => {
      if (gradeLevel) {
        return update.mutateAsync({ id: gradeLevel.id, body: { name } })
      }
      return create.mutateAsync({ name, position: nextPosition ?? 0 })
    })
  }

  return (
    <FormDialog
      open={open}
      onOpenChange={setOpen}
      trigger={trigger}
      title={gradeLevel ? 'Edit grade level' : 'Add grade level'}
      pending={pending}
      submitDisabled={name.trim() === ''}
      error={error}
      onSubmit={handleSubmit}
    >
      <div className="grid gap-2">
        <Label htmlFor="grade-level-name">Name</Label>
        <Input
          id="grade-level-name"
          value={name}
          onChange={(event) => setName(event.target.value)}
          placeholder="1st"
          autoFocus
        />
      </div>
    </FormDialog>
  )
}

export function GradeLevelsSection({ classId }: { classId: string }) {
  const gradeLevels = useGradeLevels(classId)
  const remove = useDeleteGradeLevel()
  const levels = gradeLevels.data ?? []

  return (
    <SetupSection
      title="Grade levels"
      action={
        <GradeLevelDialog
          classId={classId}
          nextPosition={levels.length + 1}
          trigger={<Button size="sm">Add</Button>}
        />
      }
    >
      {gradeLevels.error ? (
        <p className="text-sm text-destructive">Failed to load grade levels.</p>
      ) : levels.length === 0 ? (
        <p className="text-sm text-muted-foreground">
          No grade levels yet. Add at least one (e.g. “1st”).
        </p>
      ) : (
        <ul className="divide-y">
          {levels.map((level) => (
            <li key={level.id} className="flex items-center justify-between py-2">
              <span className="text-sm">{level.name}</span>
              <div className="flex gap-1">
                <GradeLevelDialog
                  classId={classId}
                  gradeLevel={level}
                  trigger={
                    <Button size="sm" variant="ghost">
                      Edit
                    </Button>
                  }
                />
                <ConfirmDialog
                  trigger={
                    <Button size="sm" variant="ghost">
                      Delete
                    </Button>
                  }
                  title="Delete grade level?"
                  description={`Remove “${level.name}”. Blocked if students are still in it.`}
                  onConfirm={() => remove.mutateAsync(level.id)}
                />
              </div>
            </li>
          ))}
        </ul>
      )}
    </SetupSection>
  )
}
