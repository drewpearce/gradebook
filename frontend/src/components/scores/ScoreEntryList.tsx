import { useEffect, useState } from 'react'

import { useDeleteScore, useSubjectScores, useUpsertScore } from '@/api/scores'
import type { components } from '@/api/schema'
import { Input } from '@/components/ui/input'
import { assignmentAppliesToStudent } from '@/lib/audience'
import { formatPoints } from '@/lib/format'

type Assignment = components['schemas']['AssignmentRead']
type GradeLevel = components['schemas']['GradeLevelRead']
type Student = components['schemas']['StudentRead']

function ScoreRow({
  label,
  subLabel,
  persisted,
  maxPoints,
  onSave,
  onClear,
}: {
  label: string
  subLabel?: string
  persisted: string | undefined
  maxPoints: string
  onSave: (value: string) => Promise<unknown>
  onClear: () => Promise<unknown>
}) {
  const display = persisted === undefined ? '' : formatPoints(persisted)
  const [value, setValue] = useState(display)
  const [error, setError] = useState<string | null>(null)

  // Re-sync when the persisted score changes (e.g. after a save refetch).
  useEffect(() => setValue(display), [display])

  function commit() {
    const trimmed = value.trim()
    if (trimmed === display) {
      setError(null)
      return
    }
    if (trimmed === '') {
      setError(null)
      if (persisted !== undefined) {
        void onClear() // blank ⇒ excluded (delete the Score), distinct from an explicit 0
      }
      return
    }
    const num = Number(trimmed)
    if (!Number.isFinite(num) || num < 0) {
      setError('Enter a number ≥ 0')
      return
    }
    setError(null)
    void onSave(trimmed)
  }

  return (
    <li className="flex items-center justify-between py-2">
      <span className="text-sm">
        {label}
        {subLabel ? (
          <span className="ml-2 text-xs text-muted-foreground">{subLabel}</span>
        ) : null}
      </span>
      <div className="flex items-center gap-2">
        <Input
          className="w-24 text-right"
          inputMode="decimal"
          placeholder="—"
          value={value}
          onChange={(event) => setValue(event.target.value)}
          onBlur={commit}
          onKeyDown={(event) => {
            if (event.key === 'Enter') {
              event.currentTarget.blur()
            }
          }}
        />
        <span className="w-16 text-xs text-muted-foreground">
          / {formatPoints(maxPoints)}
        </span>
        {error ? <span className="text-xs text-destructive">{error}</span> : null}
      </div>
    </li>
  )
}

export function ScoreEntryList({
  classId,
  subjectId,
  assignment,
  students,
  gradeLevels,
  showGradeLevel,
}: {
  classId: string
  subjectId: string
  assignment: Assignment
  students: Student[]
  gradeLevels: GradeLevel[]
  showGradeLevel: boolean
}) {
  const scoresQuery = useSubjectScores(classId, subjectId)
  const upsert = useUpsertScore(subjectId)
  const remove = useDeleteScore(subjectId)

  const applicable = students.filter((student) =>
    assignmentAppliesToStudent(student, assignment),
  )
  const scoreByStudent = new Map<string, string>()
  for (const score of scoresQuery.data ?? []) {
    if (score.assignment_id === assignment.id) {
      scoreByStudent.set(score.student_id, score.points_earned)
    }
  }

  function gradeLevelName(id: string): string {
    return gradeLevels.find((level) => level.id === id)?.name ?? ''
  }

  if (scoresQuery.error) {
    return <p className="text-sm text-destructive">Failed to load scores.</p>
  }
  if (applicable.length === 0) {
    return (
      <p className="text-sm text-muted-foreground">
        No students are in this assignment’s audience.
      </p>
    )
  }

  return (
    <div>
      <ul className="divide-y">
        {applicable.map((student) => (
          <ScoreRow
            key={student.id}
            label={student.name}
            subLabel={showGradeLevel ? gradeLevelName(student.grade_level_id) : undefined}
            persisted={scoreByStudent.get(student.id)}
            maxPoints={assignment.max_points}
            onSave={(value) =>
              upsert.mutateAsync({
                studentId: student.id,
                assignmentId: assignment.id,
                body: { points_earned: value },
              })
            }
            onClear={() =>
              remove.mutateAsync({ studentId: student.id, assignmentId: assignment.id })
            }
          />
        ))}
      </ul>
      <p className="mt-3 text-xs text-muted-foreground">
        Leave blank to exclude an assignment; enter 0 to count it as zero.
      </p>
    </div>
  )
}
