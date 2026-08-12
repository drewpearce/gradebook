import { useQuery } from '@tanstack/react-query'

import { client, unwrap } from '@/api/client'
import { useInvalidatingMutation } from '@/api/mutations'
import type { components } from '@/api/schema'

type AssignmentCreate = components['schemas']['AssignmentCreate']
type AssignmentUpdate = components['schemas']['AssignmentUpdate']

export function useAssignments(subjectId: string) {
  return useQuery({
    queryKey: ['assignments', subjectId],
    queryFn: () =>
      unwrap(
        client.GET('/subjects/{subject_id}/assignments', {
          params: { path: { subject_id: subjectId } },
        }),
      ),
  })
}

export function useCreateAssignment(subjectId: string) {
  return useInvalidatingMutation(
    (body: AssignmentCreate) =>
      unwrap(
        client.POST('/subjects/{subject_id}/assignments', {
          params: { path: { subject_id: subjectId } },
          body,
        }),
      ),
    [['assignments', subjectId]],
  )
}

export function useUpdateAssignment(subjectId: string) {
  return useInvalidatingMutation(
    ({ id, body }: { id: string; body: AssignmentUpdate }) =>
      unwrap(
        client.PATCH('/assignments/{assignment_id}', {
          params: { path: { assignment_id: id } },
          body,
        }),
      ),
    [['assignments', subjectId]],
  )
}

export function useDeleteAssignment(subjectId: string) {
  return useInvalidatingMutation(
    (id: string) =>
      unwrap(
        client.DELETE('/assignments/{assignment_id}', {
          params: { path: { assignment_id: id } },
        }),
      ),
    [['assignments', subjectId]],
  )
}
