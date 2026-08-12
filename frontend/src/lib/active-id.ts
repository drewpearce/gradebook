/** The current selection if it's still a valid option, else the first (or ''). */
export function pickActiveId(options: { id: string }[], selected: string): string {
  return options.some((option) => option.id === selected)
    ? selected
    : (options[0]?.id ?? '')
}
