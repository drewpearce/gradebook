import { useQuery } from '@tanstack/react-query'

import { client, unwrap } from '@/api/client'
import { useInvalidatingMutation } from '@/api/mutations'
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
  return useInvalidatingMutation(
    (body: CategoryCreate) =>
      unwrap(
        client.POST('/subjects/{subject_id}/categories', {
          params: { path: { subject_id: subjectId } },
          body,
        }),
      ),
    [['categories', subjectId]],
  )
}

export function useUpdateCategory(subjectId: string) {
  return useInvalidatingMutation(
    ({ id, body }: { id: string; body: CategoryUpdate }) =>
      unwrap(
        client.PATCH('/categories/{category_id}', {
          params: { path: { category_id: id } },
          body,
        }),
      ),
    [['categories', subjectId]],
  )
}

export function useDeleteCategory(subjectId: string) {
  return useInvalidatingMutation(
    (id: string) =>
      unwrap(
        client.DELETE('/categories/{category_id}', {
          params: { path: { category_id: id } },
        }),
      ),
    [['categories', subjectId]],
  )
}
