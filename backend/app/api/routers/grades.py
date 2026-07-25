from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.api.deps import SessionDep, get_or_404
from app.models import Class, Student, Subject
from app.schemas.grade import GradeResponse, RosterGrades
from app.services.grades import grade_for_student, grades_for_roster

router = APIRouter(tags=["grades"])


@router.get("/students/{student_id}/subjects/{subject_id}/grade", response_model=GradeResponse)
def get_student_subject_grade(
    student_id: UUID, subject_id: UUID, session: SessionDep
) -> GradeResponse:
    student = get_or_404(session, Student, student_id, "Student")
    subject = get_or_404(session, Subject, subject_id, "Subject")
    if subject.class_id != student.class_id:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Subject and student belong to different classes.",
        )
    return grade_for_student(session, student, subject)


@router.get("/classes/{class_id}/subjects/{subject_id}/grades", response_model=RosterGrades)
def get_roster_grades(class_id: UUID, subject_id: UUID, session: SessionDep) -> RosterGrades:
    get_or_404(session, Class, class_id, "Class")
    subject = get_or_404(session, Subject, subject_id, "Subject")
    if subject.class_id != class_id:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Subject does not belong to this class.",
        )
    students = list(
        session.scalars(select(Student).where(Student.class_id == class_id).order_by(Student.name))
    )
    return RosterGrades(subject_id=subject.id, grades=grades_for_roster(session, students, subject))
