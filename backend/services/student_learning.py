from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from core.time_utils import to_china_time
from models.answer_record import AnswerRecord
from models.student import Student
from models.task import Task
from schemas.student import (
    StudentTaskAttemptSummary,
    StudentTaskItem,
    StudentTaskQuestionResult,
    StudentTaskSummaryResponse,
)


def _calc_ratio(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0
    return round(numerator / denominator, 4)


def _resolve_task_status(progress: float, attempt_count: int) -> str:
    if attempt_count == 0:
        return "not_started"
    if progress >= 1:
        return "completed"
    return "in_progress"


def _group_records_by_task_and_session(
    rows: list[AnswerRecord],
) -> dict[int, dict[str, list[AnswerRecord]]]:
    grouped: dict[int, dict[str, list[AnswerRecord]]] = defaultdict(lambda: defaultdict(list))
    for row in rows:
        grouped[row.task_id][row.session_id].append(row)
    return grouped


def _group_records_by_session(rows: list[AnswerRecord]) -> dict[str, list[AnswerRecord]]:
    grouped: dict[str, list[AnswerRecord]] = defaultdict(list)
    for row in rows:
        grouped[row.session_id].append(row)
    return grouped


def _build_attempt_summary(
    session_id: str,
    rows: list[AnswerRecord],
    question_count: int,
) -> StudentTaskAttemptSummary:
    latest_by_question: dict[int, AnswerRecord] = {}
    for row in rows:
        latest_by_question[row.question_pk] = row

    deduped_rows = list(latest_by_question.values())
    answered_count = len(deduped_rows)
    correct_count = sum(1 for row in deduped_rows if row.is_correct)
    submitted_at = max(row.created_at for row in deduped_rows)

    return StudentTaskAttemptSummary(
        session_id=session_id,
        answered_count=answered_count,
        correct_count=correct_count,
        accuracy=_calc_ratio(correct_count, answered_count),
        progress=_calc_ratio(answered_count, question_count),
        submitted_at=to_china_time(submitted_at),
    )


def build_student_task_list(
    student: Student,
    tasks: list[Task],
    db: Session,
) -> list[StudentTaskItem]:
    if not tasks:
        return []

    task_ids = [task.id for task in tasks]
    rows = db.scalars(
        select(AnswerRecord)
        .where(
            AnswerRecord.student_no == student.student_no,
            AnswerRecord.task_id.in_(task_ids),
        )
        .order_by(
            AnswerRecord.task_id.asc(),
            AnswerRecord.created_at.asc(),
            AnswerRecord.id.asc(),
        )
    ).all()

    rows_by_task = _group_records_by_task_and_session(rows)
    task_items: list[StudentTaskItem] = []

    for task in tasks:
        grouped_sessions = rows_by_task.get(task.id, {})
        history = sorted(
            (
                _build_attempt_summary(session_id, session_rows, task.question_count)
                for session_id, session_rows in grouped_sessions.items()
            ),
            key=lambda item: item.submitted_at,
        )
        latest_attempt = history[-1] if history else None
        attempt_count = len(history)

        task_items.append(
            StudentTaskItem(
                task_id=task.id,
                title=task.title,
                grade=task.grade,
                question_count=task.question_count,
                status=task.status,
                student_task_status=_resolve_task_status(
                    latest_attempt.progress if latest_attempt else 0.0,
                    attempt_count,
                ),
                attempt_count=attempt_count,
                answered_count=latest_attempt.answered_count if latest_attempt else 0,
                correct_count=latest_attempt.correct_count if latest_attempt else 0,
                accuracy=latest_attempt.accuracy if latest_attempt else 0.0,
                progress=latest_attempt.progress if latest_attempt else 0.0,
                last_submit_at=latest_attempt.submitted_at if latest_attempt else None,
            )
        )

    return task_items


def build_student_task_summary(
    student: Student,
    task: Task,
    db: Session,
) -> StudentTaskSummaryResponse:
    task_with_questions = db.scalar(
        select(Task)
        .options(selectinload(Task.questions))
        .where(Task.id == task.id)
    )
    if not task_with_questions:
        raise ValueError(f"Task {task.id} not found")

    rows = db.scalars(
        select(AnswerRecord)
        .where(
            AnswerRecord.student_no == student.student_no,
            AnswerRecord.task_id == task.id,
        )
        .order_by(AnswerRecord.created_at.asc(), AnswerRecord.id.asc())
    ).all()

    grouped_sessions = _group_records_by_session(rows)
    history = sorted(
        (
            _build_attempt_summary(session_id, session_rows, task_with_questions.question_count)
            for session_id, session_rows in grouped_sessions.items()
        ),
        key=lambda item: item.submitted_at,
    )
    latest_attempt = history[-1] if history else None
    best_accuracy = max((item.accuracy for item in history), default=0.0)

    question_rows: dict[int, list[AnswerRecord]] = defaultdict(list)
    for row in rows:
        question_rows[row.question_pk].append(row)

    question_results = [
        StudentTaskQuestionResult(
            question_pk=question_pk,
            attempt_count=len({row.session_id for row in question_attempt_rows}),
            first_is_correct=bool(question_attempt_rows[0].is_correct),
            latest_is_correct=bool(question_attempt_rows[-1].is_correct),
            best_is_correct=any(bool(row.is_correct) for row in question_attempt_rows),
        )
        for question_pk, question_attempt_rows in sorted(question_rows.items())
    ]

    return StudentTaskSummaryResponse(
        task_id=task_with_questions.id,
        task_title=task_with_questions.title,
        student_no=student.student_no,
        student_name=student.student_name,
        question_count=task_with_questions.question_count,
        attempt_count=len(history),
        latest_attempt=latest_attempt,
        best_accuracy=best_accuracy,
        history=history,
        question_results=question_results,
    )
