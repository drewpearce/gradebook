import { useQuery } from '@tanstack/react-query'

import { client, unwrap } from '@/api/client'
import { useInvalidatingMutation } from '@/api/mutations'
import type { components } from '@/api/schema'

type SubjectCreate = components['schemas']['SubjectCreate']
type SubjectUpdate = components['schemas']['SubjectUpdate']

export function useSubjects(classId: string) {
  return useQuery({
    queryKey: ['subjects', classId],
    queryFn: () =>
      unwrap(
        client.GET('/classes/{class_id}/subjects', {
          params: { path: { class_id: classId } },
        }),
      ),
  })
}

export function useCreateSubject(classId: string) {
  return useInvalidatingMutation(
    (body: SubjectCreate) =>
      unwrap(
        client.POST('/classes/{class_id}/subjects', {
          params: { path: { class_id: classId } },
          body,
        }),
      ),
    [['subjects', classId]],
  )
}

export function useUpdateSubject(classId: string) {
  return useInvalidatingMutation(
    ({ id, body }: { id: string; body: SubjectUpdate }) =>
      unwrap(
        client.PATCH('/subjects/{subject_id}', {
          params: { path: { subject_id: id } },
          body,
        }),
      ),
    [['subjects', classId]],
  )
}

export function useDeleteSubject(classId: string) {
  return useInvalidatingMutation(
    (id: string) =>
      unwrap(
        client.DELETE('/subjects/{subject_id}', { params: { path: { subject_id: id } } }),
      ),
    [['subjects', classId]],
  )
}
