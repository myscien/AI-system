import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from models.answer_record import AnswerRecord
from models.question import Question
from models.student import Student
from models.task import Task
from schemas.analysis import (
    QuestionAnalysisItem,
    QuestionAnalysisOption,
    QuestionOptionStat,
    StudentProgressItem,
    TaskAnalysisResponse,
)

LOW_ACCURACY_THRESHOLD = 0.6
LOWEST_ACCURACY_LIMIT = 3


def _calc_accuracy(correct_count: int, total_count: int) -> float:
    if total_count == 0:
        return 0.0
    return round(correct_count / total_count, 4)


def _calc_progress(answered_count: int, total_questions: int) -> float:
    if total_questions == 0:
        return 0.0
    return round(answered_count / total_questions, 4)


def _calc_bounded_ratio(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0
    return round(min(numerator / denominator, 1.0), 4)


def _normalize_grade(grade: str) -> str:
    return grade.strip().removesuffix("\u5e74\u7ea7")


def _resolve_status(answered_count: int, total_questions: int) -> str:
    if answered_count == 0:
        return "not_started"
    if total_questions > 0 and answered_count >= total_questions:
        return "completed"
    return "in_progress"


def _load_json_list(value: str) -> list:
    try:
        parsed = json.loads(value or "[]")
    except json.JSONDecodeError:
        return []
    return parsed if isinstance(parsed, list) else []


def _build_question_options(question: Question) -> list[QuestionAnalysisOption]:
    options = []
    for item in _load_json_list(question.options_json):
        if not isinstance(item, dict):
            continue
        options.append(
            QuestionAnalysisOption(
                id=str(item.get("id", "")),
                text=str(item.get("text", "")),
                explanation=str(item.get("explanation", "")),
            )
        )
    return options


def _build_option_stats(
    question: Question,
    options: list[QuestionAnalysisOption],
    correct_answer: list[str],
    rows: list[AnswerRecord],
) -> list[QuestionOptionStat]:
    if question.question_type not in {"single_choice", "multiple_choice", "judgment"}:
        return []

    option_counts = {option.id: 0 for option in options}
    for row in rows:
        for answer_id in _load_json_list(row.student_answer_json):
            answer_id = str(answer_id)
            if answer_id in option_counts:
                option_counts[answer_id] += 1

    correct_answer_set = {str(item) for item in correct_answer}
    return [
        QuestionOptionStat(
            option_id=option.id,
            option_text=option.text,
            count=option_counts.get(option.id, 0),
            is_correct=option.id in correct_answer_set,
        )
        for option in options
    ]


def build_task_analysis(
    task_id: int,
    db: Session,
    grade: str | None = None,
    class_name: str | None = None,
) -> TaskAnalysisResponse:
    task = db.get(Task, task_id)
    if not task:
        raise ValueError(f"Task {task_id} not found")

    questions = db.scalars(
        select(Question)
        .where(Question.task_id == task_id)
        .order_by(Question.id.asc())
    ).all()
    total_questions = len(questions)

    target_grade = _normalize_grade(grade or task.grade)
    student_stmt = select(Student).where(
        Student.grade == target_grade,
        Student.status == "active",
    )
    if class_name:
        student_stmt = student_stmt.where(Student.class_name == class_name.strip())

    target_students = db.scalars(
        student_stmt.order_by(Student.grade.asc(), Student.class_name.asc(), Student.student_no.asc())
    ).all()
    student_by_no = {
        student.student_no: student
        for student in target_students
    }
    target_student_nos = set(student_by_no)

    rows = db.scalars(
        select(AnswerRecord)
        .where(
            AnswerRecord.task_id == task_id,
            AnswerRecord.student_no.in_(target_student_nos),
        )
        .order_by(AnswerRecord.created_at.asc(), AnswerRecord.id.asc())
    ).all()

    earliest_records: dict[tuple[str, int, int], AnswerRecord] = {}
    for row in rows:
        key = (row.student_no, row.task_id, row.question_pk)
        if key not in earliest_records:
            earliest_records[key] = row

    deduped_rows = list(earliest_records.values())
    rows_by_question: dict[int, list[AnswerRecord]] = {}
    for row in deduped_rows:
        rows_by_question.setdefault(row.question_pk, []).append(row)

    question_buckets: dict[int, dict] = {
        question.id: {
            "question_id": question.id,
            "question_pk": question.id,
            "total_answers": 0,
            "correct_count": 0,
        }
        for question in questions
    }
    student_buckets: dict[str, dict] = {
        student.student_no: {
            "student_no": student.student_no,
            "student_name": student.student_name,
            "grade": student.grade,
            "class_name": student.class_name,
            "answered_count": 0,
            "correct_count": 0,
        }
        for student in target_students
    }

    for row in deduped_rows:
        question_bucket = question_buckets.setdefault(
            row.question_pk,
            {
                "question_id": row.question_pk,
                "question_pk": row.question_pk,
                "total_answers": 0,
                "correct_count": 0,
            },
        )
        question_bucket["total_answers"] += 1
        if row.is_correct:
            question_bucket["correct_count"] += 1

        student_bucket = student_buckets[row.student_no]
        if not student_bucket["student_name"] and row.student_name:
            student_bucket["student_name"] = row.student_name
        student_bucket["answered_count"] += 1
        if row.is_correct:
            student_bucket["correct_count"] += 1

    question_stats = []
    question_by_id = {question.id: question for question in questions}
    for bucket in sorted(question_buckets.values(), key=lambda item: item["question_pk"]):
        question = question_by_id.get(bucket["question_pk"])
        if not question:
            continue

        options = _build_question_options(question)
        correct_answer = [str(item) for item in _load_json_list(question.correct_answer_json)]
        question_rows = rows_by_question.get(question.id, [])

        question_stats.append(
            QuestionAnalysisItem(
                question_id=bucket["question_id"],
                question_pk=bucket["question_pk"],
                knowledge_point=question.knowledge_point,
                question_type=question.question_type,
                difficulty=question.difficulty,
                stem=question.stem,
                options=options,
                correct_answer=correct_answer,
                total_answers=bucket["total_answers"],
                correct_count=bucket["correct_count"],
                wrong_count=bucket["total_answers"] - bucket["correct_count"],
                accuracy=_calc_accuracy(bucket["correct_count"], bucket["total_answers"]),
                option_stats=_build_option_stats(
                    question=question,
                    options=options,
                    correct_answer=correct_answer,
                    rows=question_rows,
                ),
            )
        )

    student_progress = [
        StudentProgressItem(
            student_no=bucket["student_no"],
            student_name=bucket["student_name"],
            grade=bucket["grade"],
            class_name=bucket["class_name"],
            answered_count=bucket["answered_count"],
            correct_count=bucket["correct_count"],
            accuracy=_calc_accuracy(bucket["correct_count"], bucket["answered_count"]),
            progress=_calc_progress(bucket["answered_count"], total_questions),
            status=_resolve_status(bucket["answered_count"], total_questions),
            is_low_accuracy=(
                bucket["answered_count"] > 0
                and _calc_accuracy(bucket["correct_count"], bucket["answered_count"]) < LOW_ACCURACY_THRESHOLD
            ),
        )
        for bucket in sorted(student_buckets.values(), key=lambda item: item["student_no"])
    ]

    assigned_students = len(target_students)
    submitted_students = sum(1 for item in student_progress if item.answered_count > 0)
    completed_students = sum(1 for item in student_progress if item.status == "completed")
    total_correct_answers = sum(item.correct_count for item in student_progress)
    total_submitted_answers = sum(item.answered_count for item in student_progress)
    low_accuracy_student_count = sum(
        1
        for item in student_progress
        if item.answered_count > 0 and item.is_low_accuracy
    )

    lowest_accuracy_questions = sorted(
        question_stats,
        key=lambda item: (item.accuracy, item.question_pk),
    )[:LOWEST_ACCURACY_LIMIT]

    return TaskAnalysisResponse(
        task_id=task_id,
        task_title=task.title,
        total_students=assigned_students,
        assigned_students=assigned_students,
        submitted_students=submitted_students,
        completed_students=completed_students,
        completion_rate=_calc_bounded_ratio(completed_students, assigned_students),
        average_accuracy=_calc_accuracy(total_correct_answers, total_submitted_answers),
        low_accuracy_student_count=low_accuracy_student_count,
        question_stats=question_stats,
        student_progress=student_progress,
        lowest_accuracy_questions=lowest_accuracy_questions,
    )
