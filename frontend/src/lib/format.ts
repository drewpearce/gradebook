/** Trim a Decimal string like "8.00" to "8" / "8.5" for display. */
export function formatPoints(value: string): string {
  const parsed = Number(value)
  return Number.isFinite(parsed) ? String(parsed) : value
}

/** Format a percentage Decimal string like "87.00" as "87%". */
export function formatPercent(value: string): string {
  return `${formatPoints(value)}%`
}

/** Join the available parts of a grade ("88.5% · B+"); either may be absent. */
export function gradeLabel(percent: string | null, letter: string | null): string {
  return [percent !== null ? formatPercent(percent) : null, letter]
    .filter((part) => part !== null)
    .join(' · ')
}

export const NOTHING_ELSE = 'Nothing else will be deleted.'

/** "12 students, 4 subjects": the non-zero counts, in `order` ([key, singular, plural]). */
export function describeCounts(
  counts: Record<string, number>,
  order: [key: string, singular: string, plural: string][],
): string {
  const parts = order
    .filter(([key]) => (counts[key] ?? 0) > 0)
    .map(
      ([key, singular, plural]) =>
        `${counts[key]} ${counts[key] === 1 ? singular : plural}`,
    )
  return parts.length > 0 ? parts.join(', ') : NOTHING_ELSE
}
