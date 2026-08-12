import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'

import { useAssignments } from '@/api/assignments'
import { useCategories } from '@/api/categories'
import { useClass } from '@/api/classes'
import { useGradeLevels } from '@/api/grade-levels'
import type { components } from '@/api/schema'
import { useStudents } from '@/api/students'
import { useSubjects } from '@/api/subjects'
import { AssignmentDialog } from '@/components/scores/AssignmentDialog'
import { ScoreEntryList } from '@/components/scores/ScoreEntryList'
import { Button } from '@/components/ui/button'
import { Label } from '@/components/ui/label'
import { Select } from '@/components/ui/select'

type GradeLevel = components['schemas']['GradeLevelRead']
type Student = components['schemas']['StudentRead']

/** Pick the current id from state, falling back to the first option. */
function useActiveId(options: { id: string }[], selected: string): string {
  return options.some((option) => option.id === selected)
    ? selected
    : (options[0]?.id ?? '')
}

function SubjectScoring({
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
  const assignmentsQuery = useAssignments(subjectId)
  const categoriesQuery = useCategories(subjectId)
  const [selectedAssignment, setSelectedAssignment] = useState('')

  const assignments = assignmentsQuery.data ?? []
  const categories = categoriesQuery.data ?? []
  const activeAssignmentId = useActiveId(assignments, selectedAssignment)
  const activeAssignment = assignments.find((a) => a.id === activeAssignmentId)
  const showGradeLevel = gradeLevels.length >= 2

  const newAssignmentButton = (
    <AssignmentDialog
      subjectId={subjectId}
      categories={categories}
      gradeLevels={gradeLevels}
      trigger={
        <Button size="sm" disabled={categories.length === 0}>
          New assignment
        </Button>
      }
    />
  )

  if (categories.length === 0) {
    return (
      <p className="text-sm text-muted-foreground">
        Add a category to this subject first, then create assignments.
      </p>
    )
  }

  return (
    <div className="space-y-4">
      <div className="flex items-end justify-between gap-4">
        {assignments.length >= 2 ? (
          <div className="grid gap-2">
            <Label htmlFor="assignment-picker">Assignment</Label>
            <Select
              id="assignment-picker"
              value={activeAssignmentId}
              onChange={(event) => setSelectedAssignment(event.target.value)}
            >
              {assignments.map((assignment) => (
                <option key={assignment.id} value={assignment.id}>
                  {assignment.name}
                </option>
              ))}
            </Select>
          </div>
        ) : (
          <h2 className="text-lg font-medium">
            {activeAssignment?.name ?? 'Assignments'}
          </h2>
        )}
        <div className="flex gap-2">
          {activeAssignment ? (
            <AssignmentDialog
              subjectId={subjectId}
              categories={categories}
              gradeLevels={gradeLevels}
              assignment={activeAssignment}
              trigger={
                <Button size="sm" variant="outline">
                  Edit
                </Button>
              }
            />
          ) : null}
          {newAssignmentButton}
        </div>
      </div>

      {assignments.length === 0 ? (
        <p className="text-sm text-muted-foreground">
          No assignments yet. Create one to score.
        </p>
      ) : activeAssignment ? (
        <ScoreEntryList
          classId={classId}
          subjectId={subjectId}
          assignment={activeAssignment}
          students={students}
          gradeLevels={gradeLevels}
          showGradeLevel={showGradeLevel}
        />
      ) : null}
    </div>
  )
}

export function ScoreEntryPage() {
  const { classId } = useParams()
  const id = classId ?? ''
  const classQuery = useClass(id)
  const subjectsQuery = useSubjects(id)
  const studentsQuery = useStudents(id)
  const gradeLevelsQuery = useGradeLevels(id)
  const [selectedSubject, setSelectedSubject] = useState('')

  const subjects = subjectsQuery.data ?? []
  const activeSubjectId = useActiveId(subjects, selectedSubject)

  if (classQuery.isPending) {
    return <p className="text-muted-foreground">Loading…</p>
  }
  if (classQuery.error || !classQuery.data) {
    return <p className="text-destructive">Class not found.</p>
  }

  return (
    <div className="space-y-6">
      <div>
        <Link
          to={`/classes/${id}`}
          className="text-sm text-muted-foreground hover:underline"
        >
          ← {classQuery.data.name}
        </Link>
        <h1 className="text-2xl font-semibold">Enter scores</h1>
      </div>

      {subjects.length === 0 ? (
        <p className="text-sm text-muted-foreground">
          Add a subject to this class first, then create assignments and enter scores.
        </p>
      ) : (
        <div className="space-y-4">
          {subjects.length >= 2 ? (
            <div className="grid max-w-xs gap-2">
              <Label htmlFor="subject-picker">Subject</Label>
              <Select
                id="subject-picker"
                value={activeSubjectId}
                onChange={(event) => setSelectedSubject(event.target.value)}
              >
                {subjects.map((subject) => (
                  <option key={subject.id} value={subject.id}>
                    {subject.name}
                  </option>
                ))}
              </Select>
            </div>
          ) : null}

          <SubjectScoring
            key={activeSubjectId}
            classId={id}
            subjectId={activeSubjectId}
            students={studentsQuery.data ?? []}
            gradeLevels={gradeLevelsQuery.data ?? []}
          />
        </div>
      )}
    </div>
  )
}
