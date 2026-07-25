from collections.abc import Sequence
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import SessionDep, commit_or_conflict, get_or_404
from app.models import Assignment, Category, Class, GradeLevel, Subject
from app.schemas.coursework import (
    AssignmentCreate,
    AssignmentRead,
    AssignmentUpdate,
    CategoryCreate,
    CategoryRead,
    CategoryUpdate,
    SubjectCreate,
    SubjectRead,
    SubjectUpdate,
)

router = APIRouter(tags=["coursework"])


# --- Subject ---------------------------------------------------------------


@router.post(
    "/classes/{class_id}/subjects",
    response_model=SubjectRead,
    status_code=status.HTTP_201_CREATED,
)
def create_subject(class_id: UUID, payload: SubjectCreate, session: SessionDep) -> Subject:
    get_or_404(session, Class, class_id, "Class")
    subject = Subject(class_id=class_id, name=payload.name)
    session.add(subject)
    commit_or_conflict(session)
    session.refresh(subject)
    return subject


@router.get("/classes/{class_id}/subjects", response_model=list[SubjectRead])
def list_subjects(class_id: UUID, session: SessionDep) -> list[Subject]:
    return list(
        session.scalars(select(Subject).where(Subject.class_id == class_id).order_by(Subject.name))
    )


@router.get("/subjects/{subject_id}", response_model=SubjectRead)
def get_subject(subject_id: UUID, session: SessionDep) -> Subject:
    return get_or_404(session, Subject, subject_id, "Subject")


@router.patch("/subjects/{subject_id}", response_model=SubjectRead)
def update_subject(subject_id: UUID, payload: SubjectUpdate, session: SessionDep) -> Subject:
    subject = get_or_404(session, Subject, subject_id, "Subject")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(subject, field, value)
    commit_or_conflict(session)
    session.refresh(subject)
    return subject


@router.delete("/subjects/{subject_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_subject(subject_id: UUID, session: SessionDep) -> None:
    session.delete(get_or_404(session, Subject, subject_id, "Subject"))
    session.commit()


# --- Category --------------------------------------------------------------


@router.post(
    "/subjects/{subject_id}/categories",
    response_model=CategoryRead,
    status_code=status.HTTP_201_CREATED,
)
def create_category(subject_id: UUID, payload: CategoryCreate, session: SessionDep) -> Category:
    get_or_404(session, Subject, subject_id, "Subject")
    category = Category(subject_id=subject_id, name=payload.name, weight=payload.weight)
    session.add(category)
    commit_or_conflict(session)
    session.refresh(category)
    return category


@router.get("/subjects/{subject_id}/categories", response_model=list[CategoryRead])
def list_categories(subject_id: UUID, session: SessionDep) -> list[Category]:
    return list(
        session.scalars(
            select(Category).where(Category.subject_id == subject_id).order_by(Category.name)
        )
    )


@router.patch("/categories/{category_id}", response_model=CategoryRead)
def update_category(category_id: UUID, payload: CategoryUpdate, session: SessionDep) -> Category:
    category = get_or_404(session, Category, category_id, "Category")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(category, field, value)
    commit_or_conflict(session)
    session.refresh(category)
    return category


@router.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(category_id: UUID, session: SessionDep) -> None:
    session.delete(get_or_404(session, Category, category_id, "Category"))
    session.commit()


# --- Assignment ------------------------------------------------------------


def _assignment_read(assignment: Assignment) -> AssignmentRead:
    return AssignmentRead(
        id=assignment.id,
        subject_id=assignment.subject_id,
        category_id=assignment.category_id,
        name=assignment.name,
        max_points=assignment.max_points,
        audience_grade_level_ids=[gl.id for gl in assignment.audience],
        created_at=assignment.created_at,
        updated_at=assignment.updated_at,
    )


def _resolve_audience(
    session: Session, subject: Subject, grade_level_ids: Sequence[UUID]
) -> list[GradeLevel]:
    """Validate that every Audience Grade Level belongs to the Subject's Class."""
    if not grade_level_ids:
        return []
    levels = list(session.scalars(select(GradeLevel).where(GradeLevel.id.in_(grade_level_ids))))
    missing = set(grade_level_ids) - {gl.id for gl in levels}
    if missing:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            detail=f"Grade level(s) not found: {sorted(map(str, missing))}",
        )
    if any(gl.class_id != subject.class_id for gl in levels):
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Audience grade levels must belong to the subject's class.",
        )
    return levels


@router.post(
    "/subjects/{subject_id}/assignments",
    response_model=AssignmentRead,
    status_code=status.HTTP_201_CREATED,
)
def create_assignment(
    subject_id: UUID, payload: AssignmentCreate, session: SessionDep
) -> AssignmentRead:
    subject = get_or_404(session, Subject, subject_id, "Subject")
    audience = _resolve_audience(session, subject, payload.audience_grade_level_ids)
    assignment = Assignment(
        subject_id=subject_id,
        category_id=payload.category_id,
        name=payload.name,
        max_points=payload.max_points,
        audience=audience,
    )
    session.add(assignment)
    commit_or_conflict(session)
    session.refresh(assignment)
    return _assignment_read(assignment)


@router.get("/subjects/{subject_id}/assignments", response_model=list[AssignmentRead])
def list_assignments(subject_id: UUID, session: SessionDep) -> list[AssignmentRead]:
    assignments = session.scalars(
        select(Assignment)
        .where(Assignment.subject_id == subject_id)
        .order_by(Assignment.name)
        .options(selectinload(Assignment.audience))
    )
    return [_assignment_read(a) for a in assignments]


@router.get("/assignments/{assignment_id}", response_model=AssignmentRead)
def get_assignment(assignment_id: UUID, session: SessionDep) -> AssignmentRead:
    return _assignment_read(get_or_404(session, Assignment, assignment_id, "Assignment"))


@router.patch("/assignments/{assignment_id}", response_model=AssignmentRead)
def update_assignment(
    assignment_id: UUID, payload: AssignmentUpdate, session: SessionDep
) -> AssignmentRead:
    assignment = get_or_404(session, Assignment, assignment_id, "Assignment")
    data = payload.model_dump(exclude_unset=True)
    if "audience_grade_level_ids" in data:
        assignment.audience = _resolve_audience(
            session, assignment.subject, data.pop("audience_grade_level_ids")
        )
    for field, value in data.items():
        setattr(assignment, field, value)
    commit_or_conflict(session)
    session.refresh(assignment)
    return _assignment_read(assignment)


@router.delete("/assignments/{assignment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_assignment(assignment_id: UUID, session: SessionDep) -> None:
    session.delete(get_or_404(session, Assignment, assignment_id, "Assignment"))
    session.commit()
