import os

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy.orm import Session

from core.database import get_db
from models.task import Task
from schemas.dify import (
    DifyCreateTaskWithQuestionsRequest,
    DifyCreateTaskWithQuestionsResponse,
)
from services.question_import import add_questions_to_task

router = APIRouter()


def _validate_dify_token(x_dify_token: str | None = Header(default=None)) -> None:
    expected_token = os.getenv("DIFY_API_TOKEN")
    if not expected_token:
        return

    if x_dify_token != expected_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Dify token",
        )


@router.post(
    "/tasks/create-with-questions",
    response_model=DifyCreateTaskWithQuestionsResponse,
    dependencies=[Depends(_validate_dify_token)],
)
def create_task_with_questions(
    payload: DifyCreateTaskWithQuestionsRequest,
    title: str | None = Query(default=None),
    grade: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    task_title = (title or payload.title or "").strip()
    task_grade = (grade or payload.grade or "").strip()
    if not task_title:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="title is required",
        )
    if not task_grade:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="grade is required",
        )

    task = Task(
        title=task_title,
        grade=task_grade,
        description=payload.description,
    )

    try:
        db.add(task)
        db.flush()

        question_items = [
            item.to_question_import_item()
            for item in payload.questions
        ]
        add_questions_to_task(task.id, question_items, db)

        db.commit()
        db.refresh(task)
    except Exception:
        db.rollback()
        raise

    question_count = len(payload.questions)
    return DifyCreateTaskWithQuestionsResponse(
        success=True,
        task_id=task.id,
        title=task.title,
        grade=task.grade,
        question_count=question_count,
        student_url="/",
        teacher_analysis_url=f"/teacher/analysis/{task.id}",
        message=f"任务创建成功，已导入 {question_count} 道题。",
    )
