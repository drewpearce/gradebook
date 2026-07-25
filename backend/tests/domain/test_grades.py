from decimal import Decimal
from uuid import UUID, uuid4

from app.domain.grades import (
    AssignmentScore,
    CategoryWeight,
    GradeInput,
    ScaleBand,
    compute_subject_grade,
    letter_for_percent,
)

# Stable ids so the scenarios read clearly.
FIRST = uuid4()
SECOND = uuid4()
HOMEWORK = uuid4()
TESTS = uuid4()


def _scale() -> list[ScaleBand]:
    return [
        ScaleBand("A", Decimal("90")),
        ScaleBand("B", Decimal("80")),
        ScaleBand("C", Decimal("70")),
        ScaleBand("D", Decimal("60")),
        ScaleBand("F", Decimal("0")),
    ]


def _hw_tests_categories() -> list[CategoryWeight]:
    return [CategoryWeight(HOMEWORK, Decimal("30")), CategoryWeight(TESTS, Decimal("70"))]


def test_mixed_audience_first_vs_second_grader() -> None:
    """The PRD scenario: HW2 targets 2nd grade only, so the two Students' Grades are
    computed over different Audiences."""
    hw1, hw2, test1 = uuid4(), uuid4(), uuid4()

    def assignments(hw2_points: Decimal | None) -> list[AssignmentScore]:
        return [
            AssignmentScore(hw1, HOMEWORK, Decimal("10"), frozenset(), Decimal("8")),
            AssignmentScore(hw2, HOMEWORK, Decimal("10"), frozenset({SECOND}), hw2_points),
            AssignmentScore(test1, TESTS, Decimal("100"), frozenset(), Decimal("90")),
        ]

    # 1st grader: HW2 is out of Audience, so HW is 8/10 = 80%.
    first = compute_subject_grade(
        GradeInput(FIRST, _hw_tests_categories(), assignments(None), _scale())
    )
    assert first.is_incomplete is False
    assert first.percent == Decimal("87.00")  # 80*0.3 + 90*0.7
    assert first.letter == "B"

    # 2nd grader: HW2 applies and is scored, so HW is 18/20 = 90%.
    second = compute_subject_grade(
        GradeInput(SECOND, _hw_tests_categories(), assignments(Decimal("10")), _scale())
    )
    assert second.percent == Decimal("90.00")  # 90*0.3 + 90*0.7
    assert second.letter == "A"


def test_incomplete_when_a_weighted_category_has_no_scored_assignment() -> None:
    hw1, test1 = uuid4(), uuid4()
    grade = compute_subject_grade(
        GradeInput(
            FIRST,
            _hw_tests_categories(),
            [
                AssignmentScore(hw1, HOMEWORK, Decimal("10"), frozenset(), Decimal("8")),
                AssignmentScore(test1, TESTS, Decimal("100"), frozenset(), None),
            ],
            _scale(),
        )
    )
    assert grade.is_incomplete is True
    assert grade.percent is None
    assert grade.letter is None
    assert TESTS in grade.incomplete_category_ids


def test_blank_is_excluded_not_zero() -> None:
    hw1, hw2 = uuid4(), uuid4()
    categories = [CategoryWeight(HOMEWORK, Decimal("100"))]

    blank = compute_subject_grade(
        GradeInput(
            FIRST,
            categories,
            [
                AssignmentScore(hw1, HOMEWORK, Decimal("10"), frozenset(), Decimal("10")),
                AssignmentScore(hw2, HOMEWORK, Decimal("10"), frozenset(), None),
            ],
            _scale(),
        )
    )
    assert blank.percent == Decimal("100.00")  # blank HW2 excluded, not 10/20

    explicit_zero = compute_subject_grade(
        GradeInput(
            FIRST,
            categories,
            [
                AssignmentScore(hw1, HOMEWORK, Decimal("10"), frozenset(), Decimal("10")),
                AssignmentScore(hw2, HOMEWORK, Decimal("10"), frozenset(), Decimal("0")),
            ],
            _scale(),
        )
    )
    assert explicit_zero.percent == Decimal("50.00")  # an explicit 0 does count


def test_extra_credit_exceeds_100_uncapped() -> None:
    assignment = uuid4()
    grade = compute_subject_grade(
        GradeInput(
            FIRST,
            [CategoryWeight(HOMEWORK, Decimal("100"))],
            [AssignmentScore(assignment, HOMEWORK, Decimal("10"), frozenset(), Decimal("12"))],
            _scale(),
        )
    )
    assert grade.percent == Decimal("120.00")
    assert grade.letter == "A"


def test_category_is_points_based_not_mean_of_percentages() -> None:
    """Unequal max_points: a Category is Σearned/Σpossible, not the average of the
    Assignments' percentages. 10/10 (100%) and 0/100 (0%) → 10/110 ≈ 9.09%, not
    the 50% a mean-of-percentages would give."""
    small, large = uuid4(), uuid4()
    grade = compute_subject_grade(
        GradeInput(
            FIRST,
            [CategoryWeight(HOMEWORK, Decimal("100"))],
            [
                AssignmentScore(small, HOMEWORK, Decimal("10"), frozenset(), Decimal("10")),
                AssignmentScore(large, HOMEWORK, Decimal("100"), frozenset(), Decimal("0")),
            ],
            _scale(),
        )
    )
    assert grade.percent == Decimal("9.09")  # 10/110*100, not 50
    assert grade.letter == "F"


def test_letter_for_percent_boundaries() -> None:
    scale = _scale()
    assert letter_for_percent(Decimal("90"), scale) == "A"
    assert letter_for_percent(Decimal("89.99"), scale) == "B"
    assert letter_for_percent(Decimal("80"), scale) == "B"
    assert letter_for_percent(Decimal("60"), scale) == "D"
    assert letter_for_percent(Decimal("59.99"), scale) == "F"
    assert letter_for_percent(Decimal("0"), scale) == "F"


def test_rounds_to_two_decimals_half_up_before_letter() -> None:
    """89.495% rounds to 89.50 and clears an A cutoff of 89.5 — exercising the
    'round to 2 dp, then apply the cutoff' decision (exact 89.495 would miss)."""
    assignment = uuid4()
    scale = [ScaleBand("A", Decimal("89.5")), ScaleBand("F", Decimal("0"))]
    grade = compute_subject_grade(
        GradeInput(
            FIRST,
            [CategoryWeight(HOMEWORK, Decimal("100"))],
            [
                AssignmentScore(
                    assignment, HOMEWORK, Decimal("1000"), frozenset(), Decimal("894.95")
                )
            ],
            scale,
        )
    )
    assert grade.percent == Decimal("89.50")
    assert grade.letter == "A"


def test_no_weighted_categories_is_incomplete() -> None:
    assignment = uuid4()
    grade = compute_subject_grade(
        GradeInput(
            FIRST,
            [CategoryWeight(HOMEWORK, Decimal("0"))],
            [AssignmentScore(assignment, HOMEWORK, Decimal("10"), frozenset(), Decimal("9"))],
            _scale(),
        )
    )
    assert grade.is_incomplete is True


def test_zero_weight_category_does_not_affect_rollup() -> None:
    extra_category: UUID = uuid4()
    hw1, extra1 = uuid4(), uuid4()
    grade = compute_subject_grade(
        GradeInput(
            FIRST,
            [
                CategoryWeight(HOMEWORK, Decimal("100")),
                CategoryWeight(extra_category, Decimal("0")),
            ],
            [
                AssignmentScore(hw1, HOMEWORK, Decimal("10"), frozenset(), Decimal("9")),
                AssignmentScore(extra1, extra_category, Decimal("10"), frozenset(), Decimal("0")),
            ],
            _scale(),
        )
    )
    assert grade.is_incomplete is False
    assert grade.percent == Decimal("90.00")  # only the weighted HW category counts
    assert grade.letter == "A"
