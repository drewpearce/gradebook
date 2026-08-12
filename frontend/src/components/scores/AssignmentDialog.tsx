import { useEffect, useState, type FormEvent, type ReactNode } from 'react'

import { useCreateAssignment, useUpdateAssignment } from '@/api/assignments'
import type { components } from '@/api/schema'
import { FormDialog } from '@/components/setup/FormDialog'
import { useDialogForm } from '@/components/setup/useDialogForm'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select } from '@/components/ui/select'

type Assignment = components['schemas']['AssignmentRead']
type Category = components['schemas']['CategoryRead']
type GradeLevel = components['schemas']['GradeLevelRead']

export function AssignmentDialog({
  subjectId,
  categories,
  gradeLevels,
  assignment,
  trigger,
}: {
  subjectId: string
  categories: Category[]
  gradeLevels: GradeLevel[]
  assignment?: Assignment
  trigger: ReactNode
}) {
  const { open, setOpen, pending, error, run } = useDialogForm()
  const [name, setName] = useState('')
  const [maxPoints, setMaxPoints] = useState('')
  const [categoryId, setCategoryId] = useState('')
  const [audienceIds, setAudienceIds] = useState<string[]>([])
  const create = useCreateAssignment(subjectId)
  const update = useUpdateAssignment(subjectId)

  useEffect(() => {
    if (open) {
      setName(assignment?.name ?? '')
      setMaxPoints(assignment?.max_points ?? '')
      setCategoryId(assignment?.category_id ?? categories[0]?.id ?? '')
      setAudienceIds(assignment?.audience_grade_level_ids ?? [])
    }
  }, [open, assignment, categories])

  // Progressive disclosure: only prompt for a Category / Audience when there's a choice.
  const showCategory = categories.length >= 2
  const showAudience = gradeLevels.length >= 2

  const points = Number(maxPoints)
  const pointsValid = maxPoints.trim() !== '' && Number.isFinite(points) && points > 0

  function toggleAudience(id: string) {
    setAudienceIds((current) =>
      current.includes(id) ? current.filter((value) => value !== id) : [...current, id],
    )
  }

  function handleSubmit(event: FormEvent) {
    event.preventDefault()
    void run(() => {
      const body = {
        name,
        max_points: maxPoints,
        category_id: categoryId,
        audience_grade_level_ids: audienceIds,
      }
      if (assignment) {
        return update.mutateAsync({ id: assignment.id, body })
      }
      return create.mutateAsync(body)
    })
  }

  return (
    <FormDialog
      open={open}
      onOpenChange={setOpen}
      trigger={trigger}
      title={assignment ? 'Edit assignment' : 'New assignment'}
      pending={pending}
      submitDisabled={name.trim() === '' || !pointsValid || categoryId === ''}
      error={error}
      onSubmit={handleSubmit}
    >
      <div className="grid gap-2">
        <Label htmlFor="assignment-name">Name</Label>
        <Input
          id="assignment-name"
          value={name}
          onChange={(event) => setName(event.target.value)}
          autoFocus
        />
      </div>
      <div className="grid gap-2">
        <Label htmlFor="assignment-max-points">Max points</Label>
        <Input
          id="assignment-max-points"
          type="number"
          min="0"
          step="any"
          value={maxPoints}
          onChange={(event) => setMaxPoints(event.target.value)}
        />
      </div>
      {showCategory ? (
        <div className="grid gap-2">
          <Label htmlFor="assignment-category">Category</Label>
          <Select
            id="assignment-category"
            value={categoryId}
            onChange={(event) => setCategoryId(event.target.value)}
          >
            {categories.map((category) => (
              <option key={category.id} value={category.id}>
                {category.name}
              </option>
            ))}
          </Select>
        </div>
      ) : null}
      {showAudience ? (
        <fieldset className="grid gap-2">
          <legend className="text-sm font-medium">Audience</legend>
          <p className="text-xs text-muted-foreground">
            Leave all unchecked to apply to every grade level.
          </p>
          {gradeLevels.map((level) => (
            <label key={level.id} className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={audienceIds.includes(level.id)}
                onChange={() => toggleAudience(level.id)}
              />
              {level.name}
            </label>
          ))}
        </fieldset>
      ) : null}
    </FormDialog>
  )
}
