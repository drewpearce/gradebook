import { useQuery } from '@tanstack/react-query'

import { client, unwrap } from '@/api/client'
import { useInvalidatingMutation } from '@/api/mutations'
import type { components } from '@/api/schema'

type GradeLevelCreate = components['schemas']['GradeLevelCreate']
type GradeLevelUpdate = components['schemas']['GradeLevelUpdate']

export function useGradeLevels(classId: string) {
  return useQuery({
    queryKey: ['grade-levels', classId],
    queryFn: () =>
      unwrap(
        client.GET('/classes/{class_id}/grade-levels', {
          params: { path: { class_id: classId } },
        }),
      ),
  })
}

export function useCreateGradeLevel(classId: string) {
  return useInvalidatingMutation((body: GradeLevelCreate) =>
    unwrap(
      client.POST('/classes/{class_id}/grade-levels', {
        params: { path: { class_id: classId } },
        body,
      }),
    ),
  )
}

export function useUpdateGradeLevel() {
  return useInvalidatingMutation(({ id, body }: { id: string; body: GradeLevelUpdate }) =>
    unwrap(
      client.PATCH('/grade-levels/{grade_level_id}', {
        params: { path: { grade_level_id: id } },
        body,
      }),
    ),
  )
}

export function useDeleteGradeLevel() {
  return useInvalidatingMutation((id: string) =>
    unwrap(
      client.DELETE('/grade-levels/{grade_level_id}', {
        params: { path: { grade_level_id: id } },
      }),
    ),
  )
}
