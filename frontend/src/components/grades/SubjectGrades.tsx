import { useState } from 'react'

import { useAssignments } from '@/api/assignments'
import { useRosterGrades } from '@/api/grades'
import type { components } from '@/api/schema'
import { useSubjectScores } from '@/api/scores'
import { Badge } from '@/components/ui/badge'
import { assignmentAppliesToStudent } from '@/lib/audience'
import { formatPercent, formatPoints } from '@/lib/format'

type Assignment = components['schemas']['AssignmentRead']
type GradeLevel = components['schemas']['GradeLevelRead']
type GradeResponse = components['schemas']['GradeResponse']
type Student = components['schemas']['StudentRead']

function StudentGradeRow({
  studentName,
  subLabel,
  grade,
  student,
  assignmentsByCategory,
  studentScores,
}: {
  studentName: string
  subLabel?: string
  grade: GradeResponse
  student: Student
  assignmentsByCategory: Map<string, Assignment[]>
  studentScores: Map<string, string>
}) {
  const [open, setOpen] = useState(false)
  const weightsReason = grade.incomplete_reasons.find(
    (reason) => reason.code === 'weights_not_100',
  )

  return (
    <li className="px-4 py-3">
      <button
        type="button"
        className="flex w-full items-center justify-between gap-4 text-left"
        onClick={() => setOpen((value) => !value)}
      >
        <span className="text-sm">
          {studentName}
          {subLabel ? (
            <span className="ml-2 text-xs text-muted-foreground">{subLabel}</span>
          ) : null}
        </span>
        {grade.is_incomplete ? (
          <Badge variant="warning">Incomplete</Badge>
        ) : (
          <Badge variant="success">
            {grade.percent ? formatPercent(grade.percent) : ''} · {grade.letter}
          </Badge>
        )}
      </button>

      {open ? (
        <div className="mt-3 space-y-3">
          {weightsReason ? (
            <p className="text-xs text-amber-700">{weightsReason.message}</p>
          ) : null}
          {grade.categories.map((category) => {
            const emptyReason = grade.incomplete_reasons.find(
              (reason) =>
                reason.code === 'empty_category' &&
                reason.category_id === category.category_id,
            )
            const applicable = (
              assignmentsByCategory.get(category.category_id) ?? []
            ).filter((assignment) => assignmentAppliesToStudent(student, assignment))
            return (
              <div key={category.category_id} className="rounded-md border p-3 text-sm">
                <div className="flex items-center justify-between">
                  <span className="font-medium">
                    {category.name}
                    <span className="ml-2 text-xs text-muted-foreground">
                      {formatPercent(category.weight)} weight
                    </span>
                  </span>
                  <span className="text-muted-foreground">
                    {category.percent
                      ? `${formatPercent(category.percent)} · ${formatPoints(category.points_earned)}/${formatPoints(category.points_possible)}`
                      : '—'}
                  </span>
                </div>
                {emptyReason ? (
                  <p className="mt-1 text-xs text-amber-700">{emptyReason.message}</p>
                ) : null}
                <ul className="mt-2 space-y-1">
                  {applicable.map((assignment) => {
                    const score = studentScores.get(assignment.id)
                    return (
                      <li key={assignment.id} className="flex justify-between text-xs">
                        <span>{assignment.name}</span>
                        {score !== undefined ? (
                          <span>
                            {formatPoints(score)}/{formatPoints(assignment.max_points)}
                          </span>
                        ) : (
                          <span className="text-muted-foreground">
                            blank — not counted
                          </span>
                        )}
                      </li>
                    )
                  })}
                  {applicable.length === 0 ? (
                    <li className="text-xs text-muted-foreground">
                      No assignments apply.
                    </li>
                  ) : null}
                </ul>
              </div>
            )
          })}
        </div>
      ) : null}
    </li>
  )
}

export function SubjectGrades({
  classId,
  subjectId,
  students,
  gradeLevels,
}: {
  classId: string
  subjectId: string
  students: Student[]
  gradeLevels: GradeLevel[]
}) {
  const rosterQuery = useRosterGrades(classId, subjectId)
  const assignmentsQuery = useAssignments(subjectId)
  const scoresQuery = useSubjectScores(classId, subjectId)

  const grades = rosterQuery.data?.grades ?? []
  const studentById = new Map(students.map((student) => [student.id, student]))
  const showGradeLevel = gradeLevels.length >= 2

  const assignmentsByCategory = new Map<string, Assignment[]>()
  for (const assignment of assignmentsQuery.data ?? []) {
    const list = assignmentsByCategory.get(assignment.category_id) ?? []
    list.push(assignment)
    assignmentsByCategory.set(assignment.category_id, list)
  }

  const scoresByStudent = new Map<string, Map<string, string>>()
  for (const score of scoresQuery.data ?? []) {
    const byAssignment =
      scoresByStudent.get(score.student_id) ?? new Map<string, string>()
    byAssignment.set(score.assignment_id, score.points_earned)
    scoresByStudent.set(score.student_id, byAssignment)
  }

  function gradeLevelName(id: string): string {
    return gradeLevels.find((level) => level.id === id)?.name ?? ''
  }

  if (rosterQuery.error) {
    return <p className="text-sm text-destructive">Failed to load grades.</p>
  }
  if (grades.length === 0) {
    return <p className="text-sm text-muted-foreground">No students yet.</p>
  }

  return (
    <ul className="divide-y rounded-md border">
      {grades.map((grade) => {
        const student = studentById.get(grade.student_id)
        if (!student) {
          return null
        }
        return (
          <StudentGradeRow
            key={grade.student_id}
            studentName={student.name}
            subLabel={showGradeLevel ? gradeLevelName(student.grade_level_id) : undefined}
            grade={grade}
            student={student}
            assignmentsByCategory={assignmentsByCategory}
            studentScores={scoresByStudent.get(grade.student_id) ?? new Map()}
          />
        )
      })}
    </ul>
  )
}
