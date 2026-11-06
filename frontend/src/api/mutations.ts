import { useMutation, useQueryClient } from '@tanstack/react-query'

/**
 * A `useMutation` that invalidates every query on success — the single seam
 * every write hook goes through. Grades depend on nearly everything, so a
 * blanket invalidation is simpler and safer than per-entity key lists. The
 * refetch is deliberately not awaited, so a save does not wait for it.
 */
export function useInvalidatingMutation<TArgs, TData>(
  mutationFn: (args: TArgs) => Promise<TData>,
) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn,
    onSuccess: () => {
      void queryClient.invalidateQueries()
    },
  })
}
