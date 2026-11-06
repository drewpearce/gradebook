from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.api.deps import SessionDep, commit_or_conflict, get_or_404
from app.domain.audience import applies_to
from app.models import Assignment, Class, Score, Student, Subject
from app.schemas.score import ScoreRead, ScoreUpsert

router = APIRouter(tags=["scores"])


@router.get(
    "/classes/{class_id}/subjects/{subject_id}/scores",
    response_model=list[ScoreRead],
)
def list_subject_scores(class_id: UUID, subject_id: UUID, session: SessionDep) -> list[Score]:
    """Every Score for a Subject's Assignments — one request to populate score entry."""
    get_or_404(session, Class, class_id, "Class")
    subject = get_or_404(session, Subject, subject_id, "Subject")
    if subject.class_id != class_id:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Subject does not belong to this class.",
        )
    return list(
        session.scalars(
            select(Score)
            .join(Assignment, Score.assignment_id == Assignment.id)
            .where(Assignment.subject_id == subject_id)
        )
    )


@router.put(
    "/students/{student_id}/assignments/{assignment_id}/score",
    response_model=ScoreRead,
)
def upsert_score(
    student_id: UUID, assignment_id: UUID, payload: ScoreUpsert, session: SessionDep
) -> Score:
    student = get_or_404(session, Student, student_id, "Student")
    assignment = get_or_404(session, Assignment, assignment_id, "Assignment")
    if assignment.subject.class_id != student.class_id:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Assignment and student belong to different classes.",
        )
    if not applies_to([gl.id for gl in assignment.audience], student.grade_level_id):
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Assignment is not in the student's audience.",
        )
    score = session.scalar(
        select(Score).where(Score.student_id == student_id, Score.assignment_id == assignment_id)
    )
    if score is None:
        score = Score(
            student_id=student_id,
            assignment_id=assignment_id,
            points_earned=payload.points_earned,
        )
        session.add(score)
    else:
        score.points_earned = payload.points_earned
    commit_or_conflict(session)
    session.refresh(score)
    return score


@router.delete(
    "/students/{student_id}/assignments/{assignment_id}/score",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_score(student_id: UUID, assignment_id: UUID, session: SessionDep) -> None:
    score = session.scalar(
        select(Score).where(Score.student_id == student_id, Score.assignment_id == assignment_id)
    )
    if score is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Score not found")
    session.delete(score)
    session.commit()
