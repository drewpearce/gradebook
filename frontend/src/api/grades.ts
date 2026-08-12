import { useQuery } from '@tanstack/react-query'

import { client, unwrap } from '@/api/client'

export function useRosterGrades(classId: string, subjectId: string) {
  return useQuery({
    queryKey: ['grades', subjectId],
    queryFn: () =>
      unwrap(
        client.GET('/classes/{class_id}/subjects/{subject_id}/grades', {
          params: { path: { class_id: classId, subject_id: subjectId } },
        }),
      ),
  })
}
