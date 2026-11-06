import { useQuery } from '@tanstack/react-query'

import { client, unwrap } from '@/api/client'
import { useInvalidatingMutation } from '@/api/mutations'
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
  return useInvalidatingMutation((body: StudentCreate) =>
    unwrap(
      client.POST('/classes/{class_id}/students', {
        params: { path: { class_id: classId } },
        body,
      }),
    ),
  )
}

export function useUpdateStudent() {
  return useInvalidatingMutation(({ id, body }: { id: string; body: StudentUpdate }) =>
    unwrap(
      client.PATCH('/students/{student_id}', {
        params: { path: { student_id: id } },
        body,
      }),
    ),
  )
}

export function useDeleteStudent() {
  return useInvalidatingMutation((id: string) =>
    unwrap(
      client.DELETE('/students/{student_id}', { params: { path: { student_id: id } } }),
    ),
  )
}
