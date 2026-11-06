import { useEffect, useId, useRef, useState } from 'react'

import { useDeleteScore, useSubjectScores, useUpsertScore } from '@/api/scores'
import type { components } from '@/api/schema'
import { QueryState } from '@/components/QueryState'
import { Input } from '@/components/ui/input'
import { assignmentAppliesToStudent } from '@/lib/audience'
import { formatPoints } from '@/lib/format'

type Assignment = components['schemas']['AssignmentRead']
type GradeLevel = components['schemas']['GradeLevelRead']
type Student = components['schemas']['StudentRead']

const SCORE_PATTERN = /^(\d+(\.\d{0,2})?|\.\d{1,2})$/

export function ScoreRow({
  label,
  subLabel,
  persisted,
  maxPoints,
  disabled,
  onSave,
  onClear,
}: {
  label: string
  subLabel?: string
  persisted: string | undefined
  maxPoints: string
  disabled?: boolean
  onSave: (value: string) => Promise<unknown>
  onClear: () => Promise<unknown>
}) {
  const display = persisted === undefined ? '' : formatPoints(persisted)
  const [value, setValue] = useState(display)
  const [error, setError] = useState<string | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)
  const errorId = useId()

  // Re-sync when the persisted score changes (e.g. after a save refetch),
  // but never overwrite what the teacher is typing.
  useEffect(() => {
    if (document.activeElement !== inputRef.current) {
      setValue(display)
    }
  }, [display])

  async function commit() {
    const trimmed = value.trim()
    if (trimmed === display) {
      setError(null)
      return
    }
    try {
      if (trimmed === '') {
        setError(null)
        if (persisted !== undefined) {
          await onClear() // blank ⇒ excluded (delete the Score), distinct from an explicit 0
        }
        return
      }
      if (!SCORE_PATTERN.test(trimmed)) {
        setError('Enter a number ≥ 0 with at most 2 decimals')
        return
      }
      setError(null)
      await onSave(trimmed)
    } catch {
      setError('Not saved. Try again.')
    }
  }

  const aboveMax =
    SCORE_PATTERN.test(value.trim()) && Number(value.trim()) > Number(maxPoints)

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
          ref={inputRef}
          className="w-24 text-right"
          inputMode="decimal"
          placeholder={disabled ? '…' : '—'}
          aria-label={`${label} score`}
          aria-invalid={error ? true : undefined}
          aria-describedby={error ? errorId : undefined}
          disabled={disabled}
          value={value}
          onChange={(event) => setValue(event.target.value)}
          onBlur={() => void commit()}
          onKeyDown={(event) => {
            if (event.key === 'Enter') {
              // Moving focus blurs this input, which saves it.
              const next = event.currentTarget
                .closest('li')
                ?.nextElementSibling?.querySelector('input')
              if (next) {
                next.focus()
              } else {
                event.currentTarget.blur()
              }
            }
          }}
        />
        <span className="w-16 text-xs text-muted-foreground">
          / {formatPoints(maxPoints)}
        </span>
        {aboveMax ? (
          <span className="text-xs text-amber-700">
            Above max ({formatPoints(maxPoints)})
          </span>
        ) : null}
        {error ? (
          <span id={errorId} className="text-xs text-destructive">
            {error}
          </span>
        ) : null}
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
  const upsert = useUpsertScore()
  const remove = useDeleteScore()

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

  if (scoresQuery.isError) {
    return <QueryState queries={[scoresQuery]}>{null}</QueryState>
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
            disabled={scoresQuery.isPending}
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
        Blank = not scored yet (not counted). 0 = scored as zero.
      </p>
    </div>
  )
}
