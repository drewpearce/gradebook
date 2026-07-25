from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import SessionDep, commit_or_conflict, get_or_404
from app.models import Class, GradeLevel, Student
from app.schemas.roster import StudentCreate, StudentRead, StudentUpdate

router = APIRouter(tags=["students"])


def _validate_grade_level(session: Session, class_id: UUID, grade_level_id: UUID) -> None:
    """A Student's Grade Level must belong to the Student's Class."""
    grade_level = session.get(GradeLevel, grade_level_id)
    if grade_level is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Grade level not found")
    if grade_level.class_id != class_id:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Grade level must belong to the student's class.",
        )


@router.post(
    "/classes/{class_id}/students",
    response_model=StudentRead,
    status_code=status.HTTP_201_CREATED,
)
def create_student(class_id: UUID, payload: StudentCreate, session: SessionDep) -> Student:
    get_or_404(session, Class, class_id, "Class")
    _validate_grade_level(session, class_id, payload.grade_level_id)
    student = Student(class_id=class_id, grade_level_id=payload.grade_level_id, name=payload.name)
    session.add(student)
    commit_or_conflict(session)
    session.refresh(student)
    return student


@router.get("/classes/{class_id}/students", response_model=list[StudentRead])
def list_students(class_id: UUID, session: SessionDep) -> list[Student]:
    return list(
        session.scalars(select(Student).where(Student.class_id == class_id).order_by(Student.name))
    )


@router.get("/students/{student_id}", response_model=StudentRead)
def get_student(student_id: UUID, session: SessionDep) -> Student:
    return get_or_404(session, Student, student_id, "Student")


@router.patch("/students/{student_id}", response_model=StudentRead)
def update_student(student_id: UUID, payload: StudentUpdate, session: SessionDep) -> Student:
    student = get_or_404(session, Student, student_id, "Student")
    data = payload.model_dump(exclude_unset=True)
    if data.get("grade_level_id") is not None:
        _validate_grade_level(session, student.class_id, data["grade_level_id"])
    for field, value in data.items():
        setattr(student, field, value)
    commit_or_conflict(session)
    session.refresh(student)
    return student


@router.delete("/students/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_student(student_id: UUID, session: SessionDep) -> None:
    session.delete(get_or_404(session, Student, student_id, "Student"))
    session.commit()
