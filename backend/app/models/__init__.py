"""ORM models. Importing this package registers every table on ``Base.metadata``."""

from app.models.class_ import Class, GradeBand, GradeLevel, GradingScale
from app.models.coursework import Assignment, Category, Subject, assignment_audience
from app.models.roster import Student
from app.models.score import Score
from app.models.teacher import Teacher

__all__ = [
    "Assignment",
    "Category",
    "Class",
    "GradeBand",
    "GradeLevel",
    "GradingScale",
    "Score",
    "Student",
    "Subject",
    "Teacher",
    "assignment_audience",
]
