import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'

import { assignment, categoryBreakdown, gradeResponse, student } from '@/test/builders'

import { StudentGradeRow } from './SubjectGrades'

type Props = Parameters<typeof StudentGradeRow>[0]

async function renderRow(overrides: Partial<Props> = {}, expand = true) {
  const s = student()
  const props: Props = {
    studentName: s.name,
    grade: gradeResponse(),
    student: s,
    assignmentsByCategory: new Map(),
    studentScores: new Map(),
    ...overrides,
  }
  render(
    <ul>
      <StudentGradeRow {...props} />
    </ul>,
  )
  if (expand) {
    await userEvent.click(screen.getByRole('button'))
  }
}

describe('StudentGradeRow', () => {
  it('shows Incomplete and no percent for an incomplete grade', async () => {
    await renderRow(
      { grade: gradeResponse({ is_incomplete: true, percent: null, letter: null }) },
      false,
    )
    expect(screen.getByText('Incomplete')).toBeInTheDocument()
    expect(screen.queryByText(/%/)).not.toBeInTheDocument()
  })

  it('shows percent and letter for a complete grade', async () => {
    await renderRow({ grade: gradeResponse({ percent: '87.00', letter: 'B' }) }, false)
    expect(screen.getByText('87% · B')).toBeInTheDocument()
    expect(screen.queryByText('Incomplete')).not.toBeInTheDocument()
  })

  it('shows an empty_category reason under its category', async () => {
    await renderRow({
      grade: gradeResponse({
        is_incomplete: true,
        categories: [categoryBreakdown({ name: 'Tests', percent: null })],
        incomplete_reasons: [
          {
            code: 'empty_category',
            category_id: 'category-1',
            message: 'Tests is empty',
          },
        ],
      }),
    })
    expect(screen.getByText('Tests is empty')).toBeInTheDocument()
  })

  it('shows a weights_not_100 reason once', async () => {
    await renderRow({
      grade: gradeResponse({
        is_incomplete: true,
        categories: [
          categoryBreakdown({ category_id: 'c1' }),
          categoryBreakdown({ category_id: 'c2', name: 'Tests' }),
        ],
        incomplete_reasons: [
          { code: 'weights_not_100', message: 'Weights must total 100' },
        ],
      }),
    })
    expect(screen.getAllByText('Weights must total 100')).toHaveLength(1)
  })

  it('shows an unscored applicable assignment as blank, not counted', async () => {
    await renderRow({
      assignmentsByCategory: new Map([['category-1', [assignment()]]]),
    })
    expect(screen.getByText('blank — not counted')).toBeInTheDocument()
  })

  it('shows an explicit score of 0 as 0 points, not blank', async () => {
    await renderRow({
      assignmentsByCategory: new Map([['category-1', [assignment()]]]),
      studentScores: new Map([['assignment-1', '0.00']]),
    })
    expect(screen.getByText('0/10')).toBeInTheDocument()
    expect(screen.queryByText('blank — not counted')).not.toBeInTheDocument()
  })

  it('does not list an assignment outside the student audience', async () => {
    await renderRow({
      assignmentsByCategory: new Map([
        ['category-1', [assignment({ audience_grade_level_ids: ['gl-other'] })]],
      ]),
    })
    expect(screen.queryByText('Quiz 1')).not.toBeInTheDocument()
  })

  it('lists an in-audience assignment but not an out-of-audience one', async () => {
    await renderRow({
      assignmentsByCategory: new Map([
        [
          'category-1',
          [
            assignment({ id: 'a1', name: 'Quiz 1', audience_grade_level_ids: ['gl-1'] }),
            assignment({
              id: 'a2',
              name: 'Quiz 2',
              audience_grade_level_ids: ['gl-other'],
            }),
          ],
        ],
      ]),
    })
    expect(screen.getByText('Quiz 1')).toBeInTheDocument()
    expect(screen.queryByText('Quiz 2')).not.toBeInTheDocument()
  })

  it('names the empty category under the Incomplete badge', async () => {
    await renderRow(
      {
        grade: gradeResponse({
          is_incomplete: true,
          categories: [categoryBreakdown({ category_id: 'c2', name: 'Tests' })],
          incomplete_reasons: [
            { code: 'empty_category', category_id: 'c2', message: 'Tests is empty' },
          ],
        }),
      },
      false,
    )
    expect(screen.getByText('Missing: Tests')).toBeInTheDocument()
  })

  it('says the weights do not total 100% under the Incomplete badge', async () => {
    await renderRow(
      {
        grade: gradeResponse({
          is_incomplete: true,
          incomplete_reasons: [{ code: 'weights_not_100', message: 'x' }],
        }),
      },
      false,
    )
    expect(screen.getByText('Weights do not total 100%')).toBeInTheDocument()
  })

  it('shows no reason line for a complete grade', async () => {
    await renderRow({}, false)
    expect(screen.queryByText(/Missing:|Weights do not/)).not.toBeInTheDocument()
  })

  it('shows Loading instead of the breakdown while details load', async () => {
    await renderRow({
      detailQueries: [{ isPending: true, isError: false, refetch: () => {} }],
    })
    expect(screen.getByText('Loading…')).toBeInTheDocument()
    expect(screen.queryByText('No assignments apply.')).not.toBeInTheDocument()
  })

  it('shows empty text for a category with no applicable assignment', async () => {
    await renderRow()
    expect(screen.getByText('No assignments apply.')).toBeInTheDocument()
  })

  it('shows the grade-level label only when one is given', async () => {
    await renderRow({ gradeLevelLabel: 'Grade 3' }, false)
    expect(screen.getByText('Grade 3')).toBeInTheDocument()
  })
})
