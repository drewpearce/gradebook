import { useQuery } from '@tanstack/react-query'

import { client, unwrap } from '@/api/client'
import { useInvalidatingMutation } from '@/api/mutations'
import type { components } from '@/api/schema'

type ClassCreate = components['schemas']['ClassCreate']
type ClassUpdate = components['schemas']['ClassUpdate']

export function useClasses() {
  return useQuery({
    queryKey: ['classes'],
    queryFn: () => unwrap(client.GET('/classes')),
  })
}

export function useClass(classId: string) {
  return useQuery({
    queryKey: ['class', classId],
    queryFn: () =>
      unwrap(
        client.GET('/classes/{class_id}', { params: { path: { class_id: classId } } }),
      ),
  })
}

export function useClassCounts(classId: string) {
  return useQuery({
    queryKey: ['class', classId, 'counts'],
    // Only called from inside delete dialogs. gcTime 0 drops the counts when the dialog
    // closes, so each open loads fresh numbers instead of flashing stale cached ones.
    staleTime: 0,
    gcTime: 0,
    queryFn: () =>
      unwrap(
        client.GET('/classes/{class_id}/counts', {
          params: { path: { class_id: classId } },
        }),
      ),
  })
}

export function useCreateClass() {
  return useInvalidatingMutation((body: ClassCreate) =>
    unwrap(client.POST('/classes', { body })),
  )
}

export function useUpdateClass(classId: string) {
  return useInvalidatingMutation((body: ClassUpdate) =>
    unwrap(
      client.PATCH('/classes/{class_id}', {
        params: { path: { class_id: classId } },
        body,
      }),
    ),
  )
}

export function useDeleteClass() {
  return useInvalidatingMutation((classId: string) =>
    unwrap(
      client.DELETE('/classes/{class_id}', { params: { path: { class_id: classId } } }),
    ),
  )
}
