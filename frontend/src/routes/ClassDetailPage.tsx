import { Link, useNavigate, useParams } from 'react-router-dom'

import { useClass, useDeleteClass } from '@/api/classes'
import { ClassDialog } from '@/components/setup/ClassDialog'
import { ConfirmDialog } from '@/components/setup/ConfirmDialog'
import { GradeLevelsSection } from '@/components/setup/GradeLevelsSection'
import { GradingScaleSection } from '@/components/setup/GradingScaleSection'
import { RosterSection } from '@/components/setup/RosterSection'
import { SubjectsSection } from '@/components/setup/SubjectsSection'
import { buttonVariants } from '@/components/ui/button-variants'
import { Button } from '@/components/ui/button'

export function ClassDetailPage() {
  const { classId } = useParams()
  const id = classId ?? ''
  const classQuery = useClass(id)
  const deleteClass = useDeleteClass()
  const navigate = useNavigate()

  if (classQuery.isPending) {
    return <p className="text-muted-foreground">Loading…</p>
  }
  if (classQuery.error || !classQuery.data) {
    return <p className="text-destructive">Class not found.</p>
  }

  const klass = classQuery.data

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <Link to="/" className="text-sm text-muted-foreground hover:underline">
            ← All classes
          </Link>
          <h1 className="text-2xl font-semibold">{klass.name}</h1>
        </div>
        <div className="flex gap-2">
          <Link
            to={`/classes/${klass.id}/grades`}
            className={buttonVariants({ variant: 'outline', size: 'sm' })}
          >
            Grades
          </Link>
          <Link
            to={`/classes/${klass.id}/scores`}
            className={buttonVariants({ size: 'sm' })}
          >
            Enter scores →
          </Link>
          <ClassDialog
            existing={klass}
            trigger={
              <Button variant="outline" size="sm">
                Rename
              </Button>
            }
          />
          <ConfirmDialog
            trigger={
              <Button variant="ghost" size="sm">
                Delete class
              </Button>
            }
            title="Delete class?"
            description={`Remove “${klass.name}” and everything in it.`}
            onConfirm={async () => {
              await deleteClass.mutateAsync(klass.id)
              navigate('/', { replace: true })
            }}
          />
        </div>
      </div>

      <GradeLevelsSection classId={klass.id} />
      <RosterSection classId={klass.id} />
      <SubjectsSection classId={klass.id} />
      <GradingScaleSection classId={klass.id} />
    </div>
  )
}
