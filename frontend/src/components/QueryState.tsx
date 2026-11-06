import type { ReactNode } from 'react'

import { Button } from '@/components/ui/button'

type QueryLike = {
  isPending: boolean
  isError: boolean
  data?: unknown
  refetch: () => unknown
}

/**
 * Shows Loading… / an error with Retry until every query has loaded, then the children.
 * A failed background refetch with data already in hand is not an error here.
 */
export function QueryState({
  queries,
  children,
}: {
  queries: QueryLike[]
  children: ReactNode
}) {
  const failed = queries.filter((query) => query.isError && query.data === undefined)
  if (failed.length > 0) {
    return (
      <div className="flex items-center gap-3 text-sm text-destructive">
        <span>Could not load this data.</span>
        <Button
          size="sm"
          variant="outline"
          onClick={() => failed.forEach((query) => void query.refetch())}
        >
          Retry
        </Button>
      </div>
    )
  }
  if (queries.some((query) => query.isPending)) {
    return <p className="text-sm text-muted-foreground">Loading…</p>
  }
  return <>{children}</>
}
