import { describe, expect, it } from 'vitest'

import { assignment, student } from '@/test/builders'

import { assignmentAppliesToStudent } from './audience'

describe('assignmentAppliesToStudent', () => {
  const s = student({ grade_level_id: 'gl-3' })

  it('applies an empty audience to every student', () => {
    expect(
      assignmentAppliesToStudent(s, assignment({ audience_grade_level_ids: [] })),
    ).toBe(true)
  })

  it('applies when the student grade level is listed', () => {
    expect(
      assignmentAppliesToStudent(
        s,
        assignment({ audience_grade_level_ids: ['gl-1', 'gl-3'] }),
      ),
    ).toBe(true)
  })

  it('does not apply when the student grade level is not listed', () => {
    expect(
      assignmentAppliesToStudent(s, assignment({ audience_grade_level_ids: ['gl-1'] })),
    ).toBe(false)
  })
})
