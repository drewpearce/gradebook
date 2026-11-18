from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import distinct, func, select

from app.api.deps import SessionDep, apply_patch, commit_or_conflict, get_or_404
from app.models import (
    Assignment,
    Category,
    Class,
    GradeBand,
    GradeLevel,
    GradingScale,
    Score,
    Student,
    Subject,
    assignment_audience,
)
from app.schemas.class_ import (
    CategoryCounts,
    ClassCounts,
    ClassCreate,
    ClassRead,
    ClassTotals,
    ClassUpdate,
    GradeLevelCreate,
    GradeLevelRead,
    GradeLevelUpdate,
    GradingScaleRead,
    GradingScaleUpsert,
    StudentCounts,
    SubjectCounts,
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
    apply_patch(class_, payload.model_dump(exclude_unset=True))
    commit_or_conflict(session)
    session.refresh(class_)
    return class_


@router.delete("/classes/{class_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_class(class_id: UUID, session: SessionDep) -> None:
    session.delete(get_or_404(session, Class, class_id, "Class"))
    session.commit()


@router.get("/classes/{class_id}/counts", response_model=ClassCounts)
def get_class_counts(class_id: UUID, session: SessionDep) -> ClassCounts:
    """Counts of what a delete would cascade to, for the delete dialogs' impact line."""
    get_or_404(session, Class, class_id, "Class")
    students = {
        id_: StudentCounts(scores=scores)
        for id_, scores in session.execute(
            select(Student.id, func.count(Score.id))
            .outerjoin(Score, Score.student_id == Student.id)
            .where(Student.class_id == class_id)
            .group_by(Student.id)
        )
    }
    subjects = {
        id_: SubjectCounts(categories=0, assignments=0, scores=0)
        for id_ in session.scalars(select(Subject.id).where(Subject.class_id == class_id))
    }
    categories: dict[UUID, CategoryCounts] = {}
    for cat_id, subject_id, assignments, scores in session.execute(
        select(
            Category.id,
            Category.subject_id,
            func.count(distinct(Assignment.id)),
            func.count(Score.id),
        )
        .join(Subject, Subject.id == Category.subject_id)
        .outerjoin(Assignment, Assignment.category_id == Category.id)
        .outerjoin(Score, Score.assignment_id == Assignment.id)
        .where(Subject.class_id == class_id)
        .group_by(Category.id, Category.subject_id)
    ):
        categories[cat_id] = CategoryCounts(assignments=assignments, scores=scores)
        subject = subjects[subject_id]
        subject.categories += 1
        subject.assignments += assignments
        subject.scores += scores
    return ClassCounts(
        totals=ClassTotals(
            students=len(students),
            subjects=len(subjects),
            categories=len(categories),
            assignments=sum(c.assignments for c in categories.values()),
            scores=sum(s.scores for s in students.values()),
        ),
        students=students,
        subjects=subjects,
        categories=categories,
    )


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
    apply_patch(grade_level, payload.model_dump(exclude_unset=True))
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
    # assignment_audience cascades on delete, which would silently turn a "2nd only"
    # Assignment into an empty Audience (= every Grade Level). Refuse instead.
    in_audience = session.scalar(
        select(assignment_audience.c.assignment_id)
        .where(assignment_audience.c.grade_level_id == grade_level_id)
        .limit(1)
    )
    if in_audience is not None:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            detail="Remove this grade level from assignment audiences first.",
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
    if not any(band.min_percent == 0 for band in payload.bands):
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="The grading scale needs a band that starts at 0%.",
        )
    scale = session.scalar(select(GradingScale).where(GradingScale.class_id == class_id))
    if scale is None:
        scale = GradingScale(class_id=class_id)
        session.add(scale)
    else:
        # Delete the old bands first: otherwise the INSERTs of the new ones run before the
        # DELETEs and trip UNIQUE(grading_scale_id, letter).
        scale.bands.clear()
        session.flush()
    scale.bands = [
        GradeBand(letter=band.letter, min_percent=band.min_percent) for band in payload.bands
    ]
    commit_or_conflict(session)
    session.refresh(scale)
    return scale
