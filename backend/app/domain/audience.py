from app.models.coursework import Assignment
from app.models.roster import Student


def assignment_applies_to_student(student: Student, assignment: Assignment) -> bool:
    """Whether an Assignment is in a Student's Audience.

    An Assignment with an empty Audience applies to every Grade Level — matching
    progressive disclosure, where a Class with a single Grade Level never sets an
    Audience. Otherwise the Assignment applies only to Students whose Grade Level
    is in the Audience. Per ADR-0002, an Assignment outside a Student's Audience is
    simply not counted for them — it is not a zero.
    """
    if not assignment.audience:
        return True
    return any(grade_level.id == student.grade_level_id for grade_level in assignment.audience)
