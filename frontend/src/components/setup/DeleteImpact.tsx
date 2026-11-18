import { useClassCounts } from '@/api/classes'
import type { components } from '@/api/schema'
import { describeCounts, NOTHING_ELSE } from '@/lib/format'

type ClassCounts = components['schemas']['ClassCounts']

const ORDER = {
  students: ['students', 'student', 'students'],
  subjects: ['subjects', 'subject', 'subjects'],
  categories: ['categories', 'category', 'categories'],
  assignments: ['assignments', 'assignment', 'assignments'],
  scores: ['scores', 'score', 'scores'],
} as const

/** "This also deletes: ..." line for a delete dialog; fetches fresh counts on mount. */
export function DeleteImpact({
  classId,
  pick,
  keys,
}: {
  classId: string
  pick: (counts: ClassCounts) => Record<string, number>
  keys: (keyof typeof ORDER)[]
}) {
  const { data, isPending, error } = useClassCounts(classId)
  if (error) {
    return <p className="text-sm text-destructive">Could not load what this deletes.</p>
  }
  if (isPending) {
    return <p className="text-sm text-muted-foreground">Checking what this deletes…</p>
  }
  const text = describeCounts(
    pick(data),
    keys.map((key) => [...ORDER[key]]),
  )
  return (
    <p className="text-sm">
      {text === NOTHING_ELSE ? text : `This also deletes: ${text}`}
    </p>
  )
}
