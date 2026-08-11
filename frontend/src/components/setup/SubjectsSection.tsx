import { useEffect, useState, type FormEvent, type ReactNode } from 'react'

import {
  useCategories,
  useCreateCategory,
  useDeleteCategory,
  useUpdateCategory,
} from '@/api/categories'
import type { components } from '@/api/schema'
import {
  useCreateSubject,
  useDeleteSubject,
  useSubjects,
  useUpdateSubject,
} from '@/api/subjects'
import { ConfirmDialog } from '@/components/setup/ConfirmDialog'
import { FormDialog } from '@/components/setup/FormDialog'
import { SetupSection } from '@/components/setup/SetupSection'
import { useDialogForm } from '@/components/setup/useDialogForm'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'

type Subject = components['schemas']['SubjectRead']
type Category = components['schemas']['CategoryRead']

function SubjectDialog({
  classId,
  subject,
  trigger,
}: {
  classId: string
  subject?: Subject
  trigger: ReactNode
}) {
  const { open, setOpen, pending, error, run } = useDialogForm()
  const [name, setName] = useState('')
  const create = useCreateSubject(classId)
  const update = useUpdateSubject(classId)

  useEffect(() => {
    if (open) {
      setName(subject?.name ?? '')
    }
  }, [open, subject])

  function handleSubmit(event: FormEvent) {
    event.preventDefault()
    void run(() => {
      if (subject) {
        return update.mutateAsync({ id: subject.id, body: { name } })
      }
      return create.mutateAsync({ name })
    })
  }

  return (
    <FormDialog
      open={open}
      onOpenChange={setOpen}
      trigger={trigger}
      title={subject ? 'Edit subject' : 'Add subject'}
      pending={pending}
      submitDisabled={name.trim() === ''}
      error={error}
      onSubmit={handleSubmit}
    >
      <div className="grid gap-2">
        <Label htmlFor="subject-name">Name</Label>
        <Input
          id="subject-name"
          value={name}
          onChange={(event) => setName(event.target.value)}
          placeholder="Math"
          autoFocus
        />
      </div>
    </FormDialog>
  )
}

function CategoryDialog({
  subjectId,
  category,
  trigger,
}: {
  subjectId: string
  category?: Category
  trigger: ReactNode
}) {
  const { open, setOpen, pending, error, run } = useDialogForm()
  const [name, setName] = useState('')
  const [weight, setWeight] = useState('')
  const create = useCreateCategory(subjectId)
  const update = useUpdateCategory(subjectId)

  useEffect(() => {
    if (open) {
      setName(category?.name ?? '')
      setWeight(category?.weight ?? '')
    }
  }, [open, category])

  function handleSubmit(event: FormEvent) {
    event.preventDefault()
    void run(() => {
      if (category) {
        return update.mutateAsync({ id: category.id, body: { name, weight } })
      }
      return create.mutateAsync({ name, weight })
    })
  }

  return (
    <FormDialog
      open={open}
      onOpenChange={setOpen}
      trigger={trigger}
      title={category ? 'Edit category' : 'Add category'}
      pending={pending}
      submitDisabled={name.trim() === '' || weight.trim() === ''}
      error={error}
      onSubmit={handleSubmit}
    >
      <div className="grid gap-2">
        <Label htmlFor="category-name">Name</Label>
        <Input
          id="category-name"
          value={name}
          onChange={(event) => setName(event.target.value)}
          placeholder="Homework"
          autoFocus
        />
      </div>
      <div className="grid gap-2">
        <Label htmlFor="category-weight">Weight (%)</Label>
        <Input
          id="category-weight"
          type="number"
          min="0"
          max="100"
          step="0.01"
          value={weight}
          onChange={(event) => setWeight(event.target.value)}
          placeholder="30"
        />
      </div>
    </FormDialog>
  )
}

function SubjectCard({ classId, subject }: { classId: string; subject: Subject }) {
  const categories = useCategories(subject.id)
  const removeSubject = useDeleteSubject(classId)
  const removeCategory = useDeleteCategory(subject.id)
  const cats = categories.data ?? []
  const total =
    Math.round(cats.reduce((sum, cat) => sum + Number(cat.weight), 0) * 100) / 100
  const totalValid = total === 100

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-3">
        <CardTitle className="text-sm">{subject.name}</CardTitle>
        <div className="flex gap-1">
          <SubjectDialog
            classId={classId}
            subject={subject}
            trigger={
              <Button size="sm" variant="ghost">
                Edit
              </Button>
            }
          />
          <ConfirmDialog
            trigger={
              <Button size="sm" variant="ghost">
                Delete
              </Button>
            }
            title="Delete subject?"
            description={`Remove “${subject.name}”, its categories, assignments, and scores.`}
            onConfirm={() => removeSubject.mutateAsync(subject.id)}
          />
        </div>
      </CardHeader>
      <CardContent>
        <div className="mb-2 flex items-center justify-between">
          <span className="text-xs font-medium text-muted-foreground">Categories</span>
          <CategoryDialog
            subjectId={subject.id}
            trigger={
              <Button size="sm" variant="outline">
                Add category
              </Button>
            }
          />
        </div>
        {categories.error ? (
          <p className="text-sm text-destructive">Failed to load categories.</p>
        ) : cats.length === 0 ? (
          <p className="text-sm text-muted-foreground">No categories yet.</p>
        ) : (
          <>
            <ul className="divide-y">
              {cats.map((cat) => (
                <li key={cat.id} className="flex items-center justify-between py-2">
                  <span className="text-sm">
                    {cat.name}
                    <span className="ml-2 text-xs text-muted-foreground">
                      {cat.weight}%
                    </span>
                  </span>
                  <div className="flex gap-1">
                    <CategoryDialog
                      subjectId={subject.id}
                      category={cat}
                      trigger={
                        <Button size="sm" variant="ghost">
                          Edit
                        </Button>
                      }
                    />
                    <ConfirmDialog
                      trigger={
                        <Button size="sm" variant="ghost">
                          Delete
                        </Button>
                      }
                      title="Delete category?"
                      description={`Remove “${cat.name}”, its assignments, and scores.`}
                      onConfirm={() => removeCategory.mutateAsync(cat.id)}
                    />
                  </div>
                </li>
              ))}
            </ul>
            <div className="mt-3 flex justify-end">
              <Badge variant={totalValid ? 'success' : 'warning'}>
                Weights total {total}%{totalValid ? '' : ' — must total 100%'}
              </Badge>
            </div>
          </>
        )}
      </CardContent>
    </Card>
  )
}

export function SubjectsSection({ classId }: { classId: string }) {
  const subjects = useSubjects(classId)
  const list = subjects.data ?? []

  return (
    <SetupSection
      title="Subjects"
      action={
        <SubjectDialog classId={classId} trigger={<Button size="sm">Add</Button>} />
      }
    >
      {subjects.error ? (
        <p className="text-sm text-destructive">Failed to load subjects.</p>
      ) : list.length === 0 ? (
        <p className="text-sm text-muted-foreground">No subjects yet.</p>
      ) : (
        <div className="space-y-3">
          {list.map((subject) => (
            <SubjectCard key={subject.id} classId={classId} subject={subject} />
          ))}
        </div>
      )}
    </SetupSection>
  )
}
