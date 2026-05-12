import json
from typing import Sequence

from sqlalchemy.orm import Session

from models.question import Question
from schemas.question import QuestionImportItem


def build_question(task_id: int, item: QuestionImportItem) -> Question:
    return Question(
        task_id=task_id,
        knowledge_point=item.knowledge_point,
        question_type=item.question_type,
        difficulty=item.difficulty,
        stem=item.stem,
        options_json=json.dumps(
            [opt.model_dump() for opt in item.options],
            ensure_ascii=False,
        ),
        correct_answer_json=json.dumps(item.correct_answer, ensure_ascii=False),
        accepted_answers_json=json.dumps(item.accepted_answers, ensure_ascii=False),
        encouragement_json=json.dumps(item.encouragement.model_dump(), ensure_ascii=False),
        student_explanation=item.student_explanation,
        score=item.score,
    )


def add_questions_to_task(
    task_id: int,
    payload: Sequence[QuestionImportItem],
    db: Session,
) -> list[Question]:
    questions = [build_question(task_id, item) for item in payload]
    db.add_all(questions)
    return questions
