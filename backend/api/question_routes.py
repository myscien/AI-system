import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from core.database import get_db
from models.task import Task
from models.question import Question
from schemas.question import QuestionImportItem, QuestionRead
from services.question_import import add_questions_to_task

router = APIRouter()

DEFAULT_ENCOURAGEMENT = {
    "correct": "",
    "wrong": "",
    "retryCorrect": "",
    "retryWrong": "",
}


@router.post("/{task_id}/questions/import")
def import_questions(
    task_id: int,
    payload: list[QuestionImportItem],
    db: Session = Depends(get_db)
):
    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # 防止重复导入同一批题目
    existing = db.scalar(
        select(Question).where(Question.task_id == task_id).limit(1)
    )
    if existing:
        raise HTTPException(status_code=400, detail="Questions already imported for this task")

    questions = add_questions_to_task(task_id, payload, db)
    db.commit()

    return {
        "message": "Questions imported successfully",
        "task_id": task_id,
        "count": len(questions)
    }


@router.get("/{task_id}/questions", response_model=list[QuestionRead])
def get_questions(task_id: int, db: Session = Depends(get_db)):
    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    rows = db.scalars(
        select(Question)
        .where(Question.task_id == task_id)
        .order_by(Question.id)
    ).all()

    result = []
    for row in rows:
        encouragement_data = DEFAULT_ENCOURAGEMENT.copy()
        encouragement_data.update(json.loads(row.encouragement_json or "{}"))
        result.append(
            QuestionRead(
                question_pk=row.id,
                knowledge_point=row.knowledge_point,
                question_type=row.question_type,
                difficulty=row.difficulty,
                stem=row.stem,
                options=json.loads(row.options_json),
                correct_answer=json.loads(row.correct_answer_json),
                accepted_answers=json.loads(row.accepted_answers_json),
                encouragement=encouragement_data,
                student_explanation=row.student_explanation,
                score=row.score,
            )
        )

    return result
