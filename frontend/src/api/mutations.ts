import { useMutation, useQueryClient, type QueryKey } from '@tanstack/react-query'

/**
 * A `useMutation` that invalidates the given query keys on success — the single
 * seam every write hook goes through, so invalidation stays consistent.
 */
export function useInvalidatingMutation<TArgs, TData>(
  mutationFn: (args: TArgs) => Promise<TData>,
  invalidateKeys: QueryKey[],
) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn,
    onSuccess: () =>
      Promise.all(
        invalidateKeys.map((queryKey) => queryClient.invalidateQueries({ queryKey })),
      ),
  })
}
