import { useQuery } from '@tanstack/react-query'

import { client, unwrap } from '@/api/client'
import { useInvalidatingMutation } from '@/api/mutations'
import type { components } from '@/api/schema'

type ScoreUpsert = components['schemas']['ScoreUpsert']

export function useSubjectScores(classId: string, subjectId: string) {
  return useQuery({
    queryKey: ['scores', subjectId],
    queryFn: () =>
      unwrap(
        client.GET('/classes/{class_id}/subjects/{subject_id}/scores', {
          params: { path: { class_id: classId, subject_id: subjectId } },
        }),
      ),
  })
}

export function useUpsertScore() {
  return useInvalidatingMutation(
    ({
      studentId,
      assignmentId,
      body,
    }: {
      studentId: string
      assignmentId: string
      body: ScoreUpsert
    }) =>
      unwrap(
        client.PUT('/students/{student_id}/assignments/{assignment_id}/score', {
          params: { path: { student_id: studentId, assignment_id: assignmentId } },
          body,
        }),
      ),
  )
}

export function useDeleteScore() {
  return useInvalidatingMutation(
    ({ studentId, assignmentId }: { studentId: string; assignmentId: string }) =>
      unwrap(
        client.DELETE('/students/{student_id}/assignments/{assignment_id}/score', {
          params: { path: { student_id: studentId, assignment_id: assignmentId } },
        }),
      ),
  )
}
