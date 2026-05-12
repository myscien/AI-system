import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from core.database import get_db
from models.answer_record import AnswerRecord
from models.task import Task
from models.question import Question
from models.student import Student
from models.submission import Submission
from models.submission_detail import SubmissionDetail
from schemas.submission import (
    SingleQuestionSubmissionCreate,
    SingleQuestionSubmissionResult,
    SubmissionCreate,
    SubmissionResult,
)
from services.scoring import score_question

router = APIRouter()


@router.post("/{task_id}/submit", response_model=SubmissionResult)
def submit_answers(task_id: int, payload: SubmissionCreate, db: Session = Depends(get_db)):
    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    question_rows = db.scalars(
        select(Question).where(Question.task_id == task_id)
    ).all()

    if not question_rows:
        raise HTTPException(status_code=400, detail="No questions found for this task")

    question_map = {q.id: q for q in question_rows}

    submission = Submission(
        task_id=task_id,
        student_name=payload.student_name,
        student_no=payload.student_no,
        total_score=0,
    )
    db.add(submission)
    db.flush()

    total_score = 0
    results = []

    for ans in payload.answers:
        question = question_map.get(ans.question_pk)
        if not question:
            continue

        result = score_question(question, ans.student_answer)
        total_score += result["score_awarded"]
        results.append(result)

        detail = SubmissionDetail(
            submission_id=submission.id,
            question_pk=result["question_pk"],
            student_answer_json=json.dumps(result["student_answer"], ensure_ascii=False),
            is_correct=1 if result["is_correct"] else 0,
            score_awarded=result["score_awarded"],
            selected_option_explanation=result["selected_option_explanation"],
            student_explanation=result["student_explanation"],
        )
        db.add(detail)

    submission.total_score = total_score
    db.commit()

    return SubmissionResult(
        task_id=task_id,
        student_name=payload.student_name,
        student_no=payload.student_no,
        total_score=total_score,
        results=results,
    )


@router.post(
    "/{task_id}/questions/{question_pk}/submit",
    response_model=SingleQuestionSubmissionResult,
)
def submit_single_question(
    task_id: int,
    question_pk: int,
    payload: SingleQuestionSubmissionCreate,
    db: Session = Depends(get_db),
):
    if not (len(payload.student_no) == 8 and payload.student_no.isdigit()):
        raise HTTPException(status_code=400, detail="student_no must be an 8-digit number")

    if not payload.session_id.strip():
        raise HTTPException(status_code=400, detail="session_id is required")

    student = db.scalar(
        select(Student).where(
            Student.student_no == payload.student_no,
            Student.status == "active",
        )
    )
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    question = db.scalar(
        select(Question).where(
            Question.task_id == task_id,
            Question.id == question_pk,
        )
    )
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    result = score_question(question, payload.student_answer)

    existing = db.scalar(
        select(AnswerRecord).where(
            AnswerRecord.task_id == task_id,
            AnswerRecord.question_pk == question_pk,
            AnswerRecord.student_no == payload.student_no,
            AnswerRecord.session_id == payload.session_id,
        )
    )

    saved = False
    message = "duplicate submission in same session ignored"

    if not existing:
        record = AnswerRecord(
            task_id=task_id,
            question_pk=question_pk,
            student_no=payload.student_no,
            student_name=student.student_name,
            session_id=payload.session_id,
            student_answer_json=json.dumps(result["student_answer"], ensure_ascii=False),
            correct_answer_json=json.dumps(result["correct_answer"], ensure_ascii=False),
            is_correct=1 if result["is_correct"] else 0,
            score_awarded=result["score_awarded"],
            selected_option_explanation=result["selected_option_explanation"],
            student_explanation=result["student_explanation"],
        )
        db.add(record)
        db.commit()
        saved = True
        message = "answer recorded"

    return SingleQuestionSubmissionResult(
        task_id=task_id,
        question_pk=question_pk,
        student_name=student.student_name,
        student_no=payload.student_no,
        student_answer=result["student_answer"],
        correct_answer=result["correct_answer"],
        is_correct=result["is_correct"],
        score_awarded=result["score_awarded"],
        saved=saved,
        message=message,
        selected_option_explanation=result["selected_option_explanation"],
        student_explanation=result["student_explanation"],
    )
