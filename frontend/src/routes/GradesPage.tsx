import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'

import { useClass } from '@/api/classes'
import { useGradeLevels } from '@/api/grade-levels'
import { useStudents } from '@/api/students'
import { useSubjects } from '@/api/subjects'
import { SubjectGrades } from '@/components/grades/SubjectGrades'
import { Label } from '@/components/ui/label'
import { Select } from '@/components/ui/select'
import { pickActiveId } from '@/lib/active-id'

export function GradesPage() {
  const { classId } = useParams()
  const id = classId ?? ''
  const classQuery = useClass(id)
  const subjectsQuery = useSubjects(id)
  const studentsQuery = useStudents(id)
  const gradeLevelsQuery = useGradeLevels(id)
  const [selectedSubject, setSelectedSubject] = useState('')

  const subjects = subjectsQuery.data ?? []
  const activeSubjectId = pickActiveId(subjects, selectedSubject)

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
        <h1 className="text-2xl font-semibold">Grades</h1>
      </div>

      {subjects.length === 0 ? (
        <p className="text-sm text-muted-foreground">
          Add a subject to this class first to see grades.
        </p>
      ) : (
        <div className="space-y-4">
          {subjects.length >= 2 ? (
            <div className="grid max-w-xs gap-2">
              <Label htmlFor="grades-subject-picker">Subject</Label>
              <Select
                id="grades-subject-picker"
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

          <SubjectGrades
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
