import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { client, unwrap } from '@/api/client'
import type { components } from '@/api/schema'

type StudentCreate = components['schemas']['StudentCreate']
type StudentUpdate = components['schemas']['StudentUpdate']

export function useStudents(classId: string) {
  return useQuery({
    queryKey: ['students', classId],
    queryFn: () =>
      unwrap(
        client.GET('/classes/{class_id}/students', {
          params: { path: { class_id: classId } },
        }),
      ),
  })
}

export function useCreateStudent(classId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (body: StudentCreate) =>
      unwrap(
        client.POST('/classes/{class_id}/students', {
          params: { path: { class_id: classId } },
          body,
        }),
      ),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['students', classId] }),
  })
}

export function useUpdateStudent(classId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, body }: { id: string; body: StudentUpdate }) =>
      unwrap(
        client.PATCH('/students/{student_id}', {
          params: { path: { student_id: id } },
          body,
        }),
      ),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['students', classId] }),
  })
}

export function useDeleteStudent(classId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) =>
      unwrap(
        client.DELETE('/students/{student_id}', { params: { path: { student_id: id } } }),
      ),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['students', classId] }),
  })
}
