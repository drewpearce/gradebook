import { Link, useNavigate } from 'react-router-dom'

import { useClasses } from '@/api/classes'
import { ClassDialog } from '@/components/setup/ClassDialog'
import { Button } from '@/components/ui/button'
import { Card, CardHeader, CardTitle } from '@/components/ui/card'

export function HomePage() {
  const classes = useClasses()
  const navigate = useNavigate()

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Classes</h1>
        <ClassDialog
          trigger={<Button size="sm">New class</Button>}
          onCreated={(created) => navigate(`/classes/${created.id}`)}
        />
      </div>

      {classes.isPending ? <p className="text-muted-foreground">Loading…</p> : null}
      {classes.error ? <p className="text-destructive">Failed to load classes.</p> : null}
      {classes.data && classes.data.length === 0 ? (
        <p className="text-muted-foreground">
          No classes yet. Create one to get started.
        </p>
      ) : null}

      <div className="grid gap-3">
        {classes.data?.map((klass) => (
          <Link key={klass.id} to={`/classes/${klass.id}`}>
            <Card className="transition-colors hover:bg-muted/50">
              <CardHeader>
                <CardTitle className="text-base">{klass.name}</CardTitle>
              </CardHeader>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  )
}
