import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { client, unwrap } from '@/api/client'
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
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (body: SubjectCreate) =>
      unwrap(
        client.POST('/classes/{class_id}/subjects', {
          params: { path: { class_id: classId } },
          body,
        }),
      ),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['subjects', classId] }),
  })
}

export function useUpdateSubject(classId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, body }: { id: string; body: SubjectUpdate }) =>
      unwrap(
        client.PATCH('/subjects/{subject_id}', {
          params: { path: { subject_id: id } },
          body,
        }),
      ),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['subjects', classId] }),
  })
}

export function useDeleteSubject(classId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) =>
      unwrap(
        client.DELETE('/subjects/{subject_id}', { params: { path: { subject_id: id } } }),
      ),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['subjects', classId] }),
  })
}
