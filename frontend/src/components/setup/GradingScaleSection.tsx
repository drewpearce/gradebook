import { useEffect, useState, type FormEvent, type ReactNode } from 'react'

import { useGradingScale, usePutGradingScale } from '@/api/grading-scale'
import type { components } from '@/api/schema'
import { FormDialog } from '@/components/setup/FormDialog'
import { SetupSection } from '@/components/setup/SetupSection'
import { useDialogForm } from '@/components/setup/useDialogForm'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'

type GradingScale = components['schemas']['GradingScaleRead']
type BandDraft = { letter: string; minPercent: string }

const DEFAULT_BANDS: BandDraft[] = [
  { letter: 'A', minPercent: '90' },
  { letter: 'B', minPercent: '80' },
  { letter: 'C', minPercent: '70' },
  { letter: 'D', minPercent: '60' },
  { letter: 'F', minPercent: '0' },
]

function GradingScaleDialog({
  classId,
  scale,
  trigger,
}: {
  classId: string
  scale: GradingScale | null
  trigger: ReactNode
}) {
  const { open, setOpen, pending, error, run } = useDialogForm()
  const [bands, setBands] = useState<BandDraft[]>(DEFAULT_BANDS)
  const put = usePutGradingScale(classId)

  useEffect(() => {
    if (open) {
      setBands(
        scale && scale.bands.length > 0
          ? scale.bands.map((band) => ({
              letter: band.letter,
              minPercent: band.min_percent,
            }))
          : DEFAULT_BANDS,
      )
    }
  }, [open, scale])

  function updateBand(index: number, patch: Partial<BandDraft>) {
    setBands((prev) =>
      prev.map((band, i) => (i === index ? { ...band, ...patch } : band)),
    )
  }

  function handleSubmit(event: FormEvent) {
    event.preventDefault()
    void run(() =>
      put.mutateAsync({
        bands: bands.map((band) => ({
          letter: band.letter,
          min_percent: band.minPercent,
        })),
      }),
    )
  }

  const valid =
    bands.length > 0 &&
    bands.every((band) => band.letter.trim() !== '' && band.minPercent.trim() !== '')

  return (
    <FormDialog
      open={open}
      onOpenChange={setOpen}
      trigger={trigger}
      title="Grading scale"
      description="Letter grades and their inclusive lower bounds. Include an F at 0%."
      pending={pending}
      submitDisabled={!valid}
      error={error}
      onSubmit={handleSubmit}
    >
      <div className="grid gap-2">
        {bands.map((band, index) => (
          // eslint-disable-next-line -- rows are positional; no stable id until saved
          <div key={index} className="flex items-center gap-2">
            <Input
              aria-label="Letter"
              value={band.letter}
              onChange={(event) => updateBand(index, { letter: event.target.value })}
              className="w-16"
              placeholder="A"
            />
            <span className="text-sm text-muted-foreground">≥</span>
            <Input
              aria-label="Minimum percent"
              type="number"
              min="0"
              max="100"
              step="0.01"
              value={band.minPercent}
              onChange={(event) => updateBand(index, { minPercent: event.target.value })}
              placeholder="90"
            />
            <span className="text-sm text-muted-foreground">%</span>
            <Button
              type="button"
              size="sm"
              variant="ghost"
              onClick={() => setBands((prev) => prev.filter((_, i) => i !== index))}
            >
              Remove
            </Button>
          </div>
        ))}
      </div>
      <Button
        type="button"
        size="sm"
        variant="outline"
        onClick={() => setBands((prev) => [...prev, { letter: '', minPercent: '' }])}
      >
        Add band
      </Button>
    </FormDialog>
  )
}

export function GradingScaleSection({ classId }: { classId: string }) {
  const scale = useGradingScale(classId)
  const bands = scale.data?.bands ?? []

  return (
    <SetupSection
      title="Grading scale"
      action={
        <GradingScaleDialog
          classId={classId}
          scale={scale.data ?? null}
          trigger={<Button size="sm">{bands.length > 0 ? 'Edit' : 'Set up'}</Button>}
        />
      }
    >
      {bands.length === 0 ? (
        <p className="text-sm text-muted-foreground">
          No grading scale yet. Set the letter cutoffs.
        </p>
      ) : (
        <ul className="flex flex-wrap gap-2">
          {bands.map((band) => (
            <li key={band.id}>
              <Badge>
                {band.letter} ≥ {band.min_percent}%
              </Badge>
            </li>
          ))}
        </ul>
      )}
    </SetupSection>
  )
}
