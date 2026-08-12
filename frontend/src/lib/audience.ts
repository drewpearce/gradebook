import type { components } from '@/api/schema'

type AssignmentRead = components['schemas']['AssignmentRead']
type StudentRead = components['schemas']['StudentRead']

/**
 * Whether an Assignment is in a Student's Audience (mirrors the backend rule and
 * `CONTEXT.md`): an empty Audience applies to every Grade Level; otherwise it
 * applies only to Students whose Grade Level is listed.
 */
export function assignmentAppliesToStudent(
  student: StudentRead,
  assignment: AssignmentRead,
): boolean {
  if (assignment.audience_grade_level_ids.length === 0) {
    return true
  }
  return assignment.audience_grade_level_ids.includes(student.grade_level_id)
}
