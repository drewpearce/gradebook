import type { components } from '@/api/schema'

type Schemas = components['schemas']

export function student(
  overrides: Partial<Schemas['StudentRead']> = {},
): Schemas['StudentRead'] {
  return {
    id: 'student-1',
    class_id: 'class-1',
    name: 'Ada',
    grade_level_id: 'gl-1',
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
    ...overrides,
  } as Schemas['StudentRead']
}

export function assignment(
  overrides: Partial<Schemas['AssignmentRead']> = {},
): Schemas['AssignmentRead'] {
  return {
    id: 'assignment-1',
    subject_id: 'subject-1',
    category_id: 'category-1',
    name: 'Quiz 1',
    max_points: '10.00',
    audience_grade_level_ids: [],
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
    ...overrides,
  } as Schemas['AssignmentRead']
}

export function categoryBreakdown(
  overrides: Partial<Schemas['CategoryBreakdown']> = {},
): Schemas['CategoryBreakdown'] {
  return {
    category_id: 'category-1',
    name: 'Homework',
    weight: '100.00',
    percent: '80.00',
    points_earned: '8.00',
    points_possible: '10.00',
    scored_count: 1,
    ...overrides,
  } as Schemas['CategoryBreakdown']
}

export function gradeResponse(
  overrides: Partial<Schemas['GradeResponse']> = {},
): Schemas['GradeResponse'] {
  return {
    student_id: 'student-1',
    subject_id: 'subject-1',
    percent: '80.00',
    letter: 'B',
    is_incomplete: false,
    incomplete_reasons: [],
    categories: [categoryBreakdown()],
    ...overrides,
  } as Schemas['GradeResponse']
}
