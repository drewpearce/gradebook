import { useClasses } from '@/api/hooks'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

export function HomePage() {
  const classes = useClasses()

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold">Classes</h1>

      {classes.isPending ? <p className="text-muted-foreground">Loading…</p> : null}
      {classes.error ? <p className="text-destructive">Failed to load classes.</p> : null}
      {classes.data && classes.data.length === 0 ? (
        <p className="text-muted-foreground">No classes yet.</p>
      ) : null}

      <div className="grid gap-3">
        {classes.data?.map((klass) => (
          <Card key={klass.id}>
            <CardHeader>
              <CardTitle className="text-base">{klass.name}</CardTitle>
            </CardHeader>
            <CardContent className="text-sm text-muted-foreground">
              Created {new Date(klass.created_at).toLocaleDateString()}
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}
