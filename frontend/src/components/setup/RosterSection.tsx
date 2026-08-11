import { useEffect, useState, type FormEvent, type ReactNode } from 'react'

import { useGradeLevels } from '@/api/grade-levels'
import type { components } from '@/api/schema'
import {
  useCreateStudent,
  useDeleteStudent,
  useStudents,
  useUpdateStudent,
} from '@/api/students'
import { ConfirmDialog } from '@/components/setup/ConfirmDialog'
import { FormDialog } from '@/components/setup/FormDialog'
import { SetupSection } from '@/components/setup/SetupSection'
import { useDialogForm } from '@/components/setup/useDialogForm'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select } from '@/components/ui/select'

type Student = components['schemas']['StudentRead']
type GradeLevel = components['schemas']['GradeLevelRead']

function StudentDialog({
  classId,
  gradeLevels,
  student,
  trigger,
}: {
  classId: string
  gradeLevels: GradeLevel[]
  student?: Student
  trigger: ReactNode
}) {
  const { open, setOpen, pending, error, run } = useDialogForm()
  const [name, setName] = useState('')
  const [gradeLevelId, setGradeLevelId] = useState('')
  const create = useCreateStudent(classId)
  const update = useUpdateStudent(classId)

  useEffect(() => {
    if (open) {
      setName(student?.name ?? '')
      setGradeLevelId(student?.grade_level_id ?? gradeLevels[0]?.id ?? '')
    }
  }, [open, student, gradeLevels])

  // Progressive disclosure: only prompt for a Grade Level when there's a choice.
  const showPicker = gradeLevels.length >= 2

  function handleSubmit(event: FormEvent) {
    event.preventDefault()
    void run(() => {
      if (student) {
        return update.mutateAsync({
          id: student.id,
          body: { name, grade_level_id: gradeLevelId },
        })
      }
      return create.mutateAsync({ name, grade_level_id: gradeLevelId })
    })
  }

  return (
    <FormDialog
      open={open}
      onOpenChange={setOpen}
      trigger={trigger}
      title={student ? 'Edit student' : 'Add student'}
      pending={pending}
      submitDisabled={name.trim() === '' || gradeLevelId === ''}
      error={error}
      onSubmit={handleSubmit}
    >
      <div className="grid gap-2">
        <Label htmlFor="student-name">Name</Label>
        <Input
          id="student-name"
          value={name}
          onChange={(event) => setName(event.target.value)}
          autoFocus
        />
      </div>
      {showPicker ? (
        <div className="grid gap-2">
          <Label htmlFor="student-grade-level">Grade level</Label>
          <Select
            id="student-grade-level"
            value={gradeLevelId}
            onChange={(event) => setGradeLevelId(event.target.value)}
          >
            {gradeLevels.map((level) => (
              <option key={level.id} value={level.id}>
                {level.name}
              </option>
            ))}
          </Select>
        </div>
      ) : null}
    </FormDialog>
  )
}

export function RosterSection({ classId }: { classId: string }) {
  const gradeLevels = useGradeLevels(classId)
  const students = useStudents(classId)
  const remove = useDeleteStudent(classId)
  const levels = gradeLevels.data ?? []
  const roster = students.data ?? []
  const showGradeLevel = levels.length >= 2

  function gradeLevelName(id: string): string {
    return levels.find((level) => level.id === id)?.name ?? '—'
  }

  return (
    <SetupSection
      title="Students"
      action={
        <StudentDialog
          classId={classId}
          gradeLevels={levels}
          trigger={
            <Button size="sm" disabled={levels.length === 0}>
              Add
            </Button>
          }
        />
      }
    >
      {students.error ? (
        <p className="text-sm text-destructive">Failed to load students.</p>
      ) : levels.length === 0 ? (
        <p className="text-sm text-muted-foreground">
          Add a grade level first, then add students.
        </p>
      ) : roster.length === 0 ? (
        <p className="text-sm text-muted-foreground">No students yet.</p>
      ) : (
        <ul className="divide-y">
          {roster.map((student) => (
            <li key={student.id} className="flex items-center justify-between py-2">
              <span className="text-sm">
                {student.name}
                {showGradeLevel ? (
                  <span className="ml-2 text-xs text-muted-foreground">
                    {gradeLevelName(student.grade_level_id)}
                  </span>
                ) : null}
              </span>
              <div className="flex gap-1">
                <StudentDialog
                  classId={classId}
                  gradeLevels={levels}
                  student={student}
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
                  title="Delete student?"
                  description={`Remove “${student.name}” and their scores.`}
                  onConfirm={() => remove.mutateAsync(student.id)}
                />
              </div>
            </li>
          ))}
        </ul>
      )}
    </SetupSection>
  )
}
