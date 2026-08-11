import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { client, unwrap } from '@/api/client'
import type { components } from '@/api/schema'

type CategoryCreate = components['schemas']['CategoryCreate']
type CategoryUpdate = components['schemas']['CategoryUpdate']

export function useCategories(subjectId: string) {
  return useQuery({
    queryKey: ['categories', subjectId],
    queryFn: () =>
      unwrap(
        client.GET('/subjects/{subject_id}/categories', {
          params: { path: { subject_id: subjectId } },
        }),
      ),
  })
}

export function useCreateCategory(subjectId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (body: CategoryCreate) =>
      unwrap(
        client.POST('/subjects/{subject_id}/categories', {
          params: { path: { subject_id: subjectId } },
          body,
        }),
      ),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: ['categories', subjectId] }),
  })
}

export function useUpdateCategory(subjectId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, body }: { id: string; body: CategoryUpdate }) =>
      unwrap(
        client.PATCH('/categories/{category_id}', {
          params: { path: { category_id: id } },
          body,
        }),
      ),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: ['categories', subjectId] }),
  })
}

export function useDeleteCategory(subjectId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: string) =>
      unwrap(
        client.DELETE('/categories/{category_id}', {
          params: { path: { category_id: id } },
        }),
      ),
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: ['categories', subjectId] }),
  })
}
