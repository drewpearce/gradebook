import { useQuery } from '@tanstack/react-query'

import { client, unwrap } from '@/api/client'
import { useInvalidatingMutation } from '@/api/mutations'
import type { components } from '@/api/schema'

type GradingScaleUpsert = components['schemas']['GradingScaleUpsert']

export function useGradingScale(classId: string) {
  return useQuery({
    queryKey: ['grading-scale', classId],
    queryFn: async () => {
      const { data, error, response } = await client.GET(
        '/classes/{class_id}/grading-scale',
        {
          params: { path: { class_id: classId } },
        },
      )
      if (response.status === 404) {
        return null // No Grading Scale set yet — a valid, expected state during setup.
      }
      if (error) {
        throw error
      }
      return data ?? null
    },
  })
}

export function usePutGradingScale(classId: string) {
  return useInvalidatingMutation((body: GradingScaleUpsert) =>
    unwrap(
      client.PUT('/classes/{class_id}/grading-scale', {
        params: { path: { class_id: classId } },
        body,
      }),
    ),
  )
}
