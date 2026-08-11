import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { client, unwrap } from '@/api/client'
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

export function useCreateClass() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (body: ClassCreate) => unwrap(client.POST('/classes', { body })),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['classes'] }),
  })
}

export function useUpdateClass(classId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (body: ClassUpdate) =>
      unwrap(
        client.PATCH('/classes/{class_id}', {
          params: { path: { class_id: classId } },
          body,
        }),
      ),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['classes'] })
      void queryClient.invalidateQueries({ queryKey: ['class', classId] })
    },
  })
}

export function useDeleteClass() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (classId: string) =>
      unwrap(
        client.DELETE('/classes/{class_id}', { params: { path: { class_id: classId } } }),
      ),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['classes'] }),
  })
}
