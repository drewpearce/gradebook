import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { client, unwrap } from '@/api/client'
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
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (body: GradeLevelCreate) =>
      unwrap(
        client.POST('/classes/{class_id}/grade-levels', {
          params: { path: { class_id: classId } },
          body,
        }),
      ),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: ['grade-levels', classId] }),
  })
}

export function useUpdateGradeLevel(classId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, body }: { id: string; body: GradeLevelUpdate }) =>
      unwrap(
        client.PATCH('/grade-levels/{grade_level_id}', {
          params: { path: { grade_level_id: id } },
          body,
        }),
      ),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: ['grade-levels', classId] }),
  })
}

export function useDeleteGradeLevel(classId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) =>
      unwrap(
        client.DELETE('/grade-levels/{grade_level_id}', {
          params: { path: { grade_level_id: id } },
        }),
      ),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: ['grade-levels', classId] }),
  })
}
