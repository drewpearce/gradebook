from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.api.deps import SessionDep, commit_or_conflict, get_or_404
from app.models import Class, GradeBand, GradeLevel, GradingScale, Student
from app.schemas.class_ import (
    ClassCreate,
    ClassRead,
    ClassUpdate,
    GradeLevelCreate,
    GradeLevelRead,
    GradeLevelUpdate,
    GradingScaleRead,
    GradingScaleUpsert,
)

router = APIRouter(tags=["classes"])


# --- Class -----------------------------------------------------------------


@router.post("/classes", response_model=ClassRead, status_code=status.HTTP_201_CREATED)
def create_class(payload: ClassCreate, session: SessionDep) -> Class:
    class_ = Class(name=payload.name)
    session.add(class_)
    commit_or_conflict(session)
    session.refresh(class_)
    return class_


@router.get("/classes", response_model=list[ClassRead])
def list_classes(session: SessionDep) -> list[Class]:
    return list(session.scalars(select(Class).order_by(Class.name)))


@router.get("/classes/{class_id}", response_model=ClassRead)
def get_class(class_id: UUID, session: SessionDep) -> Class:
    return get_or_404(session, Class, class_id, "Class")


@router.patch("/classes/{class_id}", response_model=ClassRead)
def update_class(class_id: UUID, payload: ClassUpdate, session: SessionDep) -> Class:
    class_ = get_or_404(session, Class, class_id, "Class")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(class_, field, value)
    commit_or_conflict(session)
    session.refresh(class_)
    return class_


@router.delete("/classes/{class_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_class(class_id: UUID, session: SessionDep) -> None:
    session.delete(get_or_404(session, Class, class_id, "Class"))
    session.commit()


# --- Grade Level -----------------------------------------------------------


@router.post(
    "/classes/{class_id}/grade-levels",
    response_model=GradeLevelRead,
    status_code=status.HTTP_201_CREATED,
)
def create_grade_level(
    class_id: UUID, payload: GradeLevelCreate, session: SessionDep
) -> GradeLevel:
    get_or_404(session, Class, class_id, "Class")
    grade_level = GradeLevel(class_id=class_id, name=payload.name, position=payload.position)
    session.add(grade_level)
    commit_or_conflict(session)
    session.refresh(grade_level)
    return grade_level


@router.get("/classes/{class_id}/grade-levels", response_model=list[GradeLevelRead])
def list_grade_levels(class_id: UUID, session: SessionDep) -> list[GradeLevel]:
    get_or_404(session, Class, class_id, "Class")
    return list(
        session.scalars(
            select(GradeLevel)
            .where(GradeLevel.class_id == class_id)
            .order_by(GradeLevel.position, GradeLevel.name)
        )
    )


@router.patch("/grade-levels/{grade_level_id}", response_model=GradeLevelRead)
def update_grade_level(
    grade_level_id: UUID, payload: GradeLevelUpdate, session: SessionDep
) -> GradeLevel:
    grade_level = get_or_404(session, GradeLevel, grade_level_id, "Grade level")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(grade_level, field, value)
    commit_or_conflict(session)
    session.refresh(grade_level)
    return grade_level


@router.delete("/grade-levels/{grade_level_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_grade_level(grade_level_id: UUID, session: SessionDep) -> None:
    grade_level = get_or_404(session, GradeLevel, grade_level_id, "Grade level")
    # A Grade Level is a label Students reference, not a container of them: deleting
    # one would silently cascade its Students (and their Scores) away. Refuse instead.
    referenced = session.scalar(
        select(Student.id).where(Student.grade_level_id == grade_level_id).limit(1)
    )
    if referenced is not None:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            detail="Cannot delete a grade level that still has students; reassign them first.",
        )
    session.delete(grade_level)
    session.commit()


# --- Grading Scale (1:1 with Class) ----------------------------------------


@router.get("/classes/{class_id}/grading-scale", response_model=GradingScaleRead)
def get_grading_scale(class_id: UUID, session: SessionDep) -> GradingScale:
    get_or_404(session, Class, class_id, "Class")
    scale = session.scalar(select(GradingScale).where(GradingScale.class_id == class_id))
    if scale is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Grading scale not set")
    return scale


@router.put("/classes/{class_id}/grading-scale", response_model=GradingScaleRead)
def put_grading_scale(
    class_id: UUID, payload: GradingScaleUpsert, session: SessionDep
) -> GradingScale:
    get_or_404(session, Class, class_id, "Class")
    scale = session.scalar(select(GradingScale).where(GradingScale.class_id == class_id))
    if scale is None:
        scale = GradingScale(class_id=class_id)
        session.add(scale)
    scale.bands = [
        GradeBand(letter=band.letter, min_percent=band.min_percent) for band in payload.bands
    ]
    commit_or_conflict(session)
    session.refresh(scale)
    return scale
