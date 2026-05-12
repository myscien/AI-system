import csv
import io
import json

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy import delete, select
from sqlalchemy.orm import Session, selectinload

from core.database import get_db
from models.answer_record import AnswerRecord
from models.question import Question
from models.student import Student
from models.submission import Submission
from models.submission_detail import SubmissionDetail
from models.task import Task
from schemas.question import QuestionImportItem, QuestionRead, QuestionUpdate
from schemas.student import (
    StudentImportItem,
    StudentImportResult,
    StudentListResponse,
    StudentRead,
)
from schemas.teacher import (
    TeacherQuestionImportResult,
    TeacherTaskCreate,
    TeacherTaskRead,
    TeacherTaskUpdate,
)
from services.question_import import add_questions_to_task

router = APIRouter()

DEFAULT_ENCOURAGEMENT = {
    "correct": "",
    "wrong": "",
    "retryCorrect": "",
    "retryWrong": "",
}


def _normalize_grade(grade: str) -> str:
    return grade.strip().removesuffix("\u5e74\u7ea7")


def _validate_student_no(student_no: str) -> None:
    if not (len(student_no) == 8 and student_no.isdigit()):
        raise HTTPException(status_code=400, detail="student_no must be an 8-digit number")


def _to_question_read(question: Question) -> QuestionRead:
    encouragement_data = DEFAULT_ENCOURAGEMENT.copy()
    encouragement_data.update(json.loads(question.encouragement_json or "{}"))
    return QuestionRead(
        question_pk=question.id,
        knowledge_point=question.knowledge_point,
        question_type=question.question_type,
        difficulty=question.difficulty,
        stem=question.stem,
        options=json.loads(question.options_json),
        correct_answer=json.loads(question.correct_answer_json),
        accepted_answers=json.loads(question.accepted_answers_json),
        encouragement=encouragement_data,
        student_explanation=question.student_explanation,
        score=question.score,
    )


def _import_student_items(
    payload: list[StudentImportItem],
    db: Session,
) -> StudentImportResult:
    deduped_items: dict[str, StudentImportItem] = {}
    for item in payload:
        _validate_student_no(item.student_no)
        deduped_items[item.student_no] = item

    created_count = 0
    updated_count = 0

    for item in deduped_items.values():
        existing = db.scalar(
            select(Student).where(Student.student_no == item.student_no)
        )
        if existing:
            existing.student_name = item.student_name
            existing.grade = _normalize_grade(item.grade)
            existing.class_name = item.class_name
            existing.status = item.status
            updated_count += 1
            continue

        db.add(
            Student(
                student_no=item.student_no,
                student_name=item.student_name,
                grade=_normalize_grade(item.grade),
                class_name=item.class_name,
                status=item.status,
            )
        )
        created_count += 1

    db.commit()

    return StudentImportResult(
        message="Students imported successfully",
        count=len(payload),
        created_count=created_count,
        updated_count=updated_count,
    )


def _decode_csv_content(content: bytes) -> str:
    for encoding in ("utf-8-sig", "gb18030"):
        try:
            return content.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise HTTPException(status_code=400, detail="CSV file encoding must be UTF-8 or GB18030")


def _parse_student_csv(content: bytes) -> list[StudentImportItem]:
    text = _decode_csv_content(content)
    reader = csv.DictReader(io.StringIO(text))

    if not reader.fieldnames:
        raise HTTPException(status_code=400, detail="CSV file must include a header row")

    header_aliases = {
        "student_no": {"student_no", "\u5b66\u53f7"},
        "student_name": {"student_name", "\u59d3\u540d", "\u5b66\u751f\u59d3\u540d"},
        "grade": {"grade", "\u5e74\u7ea7"},
        "class_name": {"class_name", "\u73ed\u7ea7"},
        "status": {"status", "\u72b6\u6001"},
    }
    fieldnames = {field.strip() for field in reader.fieldnames if field}
    field_map: dict[str, str] = {}
    for canonical_name, aliases in header_aliases.items():
        for alias in aliases:
            if alias in fieldnames:
                field_map[canonical_name] = alias
                break

    required_fields = {"student_no", "student_name", "grade", "class_name"}
    missing_fields = sorted(required_fields - set(field_map))
    if missing_fields:
        raise HTTPException(
            status_code=400,
            detail=f"CSV missing required columns: {', '.join(missing_fields)}",
        )

    students: list[StudentImportItem] = []
    for row_number, row in enumerate(reader, start=2):
        normalized_row = {
            key.strip(): (value.strip() if value else "")
            for key, value in row.items()
            if key
        }
        if not any(normalized_row.values()):
            continue

        student_no = normalized_row.get(field_map["student_no"], "")
        student_name = normalized_row.get(field_map["student_name"], "")
        grade = normalized_row.get(field_map["grade"], "")
        class_name = normalized_row.get(field_map["class_name"], "")
        status = normalized_row.get(field_map.get("status", ""), "") or "active"

        missing_values = [
            field_name
            for field_name, field_value in (
                ("student_no", student_no),
                ("student_name", student_name),
                ("grade", grade),
                ("class_name", class_name),
            )
            if not field_value
        ]
        if missing_values:
            raise HTTPException(
                status_code=400,
                detail=f"CSV row {row_number} missing values: {', '.join(missing_values)}",
            )

        students.append(
            StudentImportItem(
                student_no=student_no,
                student_name=student_name,
                grade=grade,
                class_name=class_name,
                status=status,
            )
        )

    if not students:
        raise HTTPException(status_code=400, detail="CSV file has no student rows")

    return students


@router.get("/tasks", response_model=list[TeacherTaskRead])
def list_teacher_tasks(db: Session = Depends(get_db)):
    tasks = db.scalars(
        select(Task)
        .options(selectinload(Task.questions))
        .order_by(Task.id.desc())
    ).all()
    return tasks


@router.post("/tasks", response_model=TeacherTaskRead)
def create_teacher_task(payload: TeacherTaskCreate, db: Session = Depends(get_db)):
    task = Task(
        title=payload.title,
        grade=_normalize_grade(payload.grade),
        description=payload.description,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@router.patch("/tasks/{task_id}", response_model=TeacherTaskRead)
def update_teacher_task(
    task_id: int,
    payload: TeacherTaskUpdate,
    db: Session = Depends(get_db),
):
    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    data = payload.model_dump(exclude_unset=True)
    if "grade" in data:
        data["grade"] = _normalize_grade(data["grade"])

    for key, value in data.items():
        setattr(task, key, value)

    db.commit()
    db.refresh(task)
    return task


@router.delete("/tasks/{task_id}")
def delete_teacher_task(task_id: int, db: Session = Depends(get_db)):
    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    question_ids = db.scalars(
        select(Question.id).where(Question.task_id == task_id)
    ).all()
    submission_ids = db.scalars(
        select(Submission.id).where(Submission.task_id == task_id)
    ).all()

    if submission_ids:
        db.execute(
            delete(SubmissionDetail).where(
                SubmissionDetail.submission_id.in_(submission_ids)
            )
        )

    if question_ids:
        db.execute(
            delete(AnswerRecord).where(AnswerRecord.question_pk.in_(question_ids))
        )
        db.execute(delete(Question).where(Question.id.in_(question_ids)))

    db.execute(delete(Submission).where(Submission.task_id == task_id))
    db.delete(task)
    db.commit()

    return {"message": "Task deleted successfully", "task_id": task_id}


@router.post(
    "/tasks/{task_id}/questions/import",
    response_model=TeacherQuestionImportResult,
)
def import_teacher_questions(
    task_id: int,
    payload: list[QuestionImportItem],
    db: Session = Depends(get_db),
):
    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    questions = add_questions_to_task(task_id, payload, db)

    db.commit()

    return TeacherQuestionImportResult(
        message="Questions imported successfully",
        task_id=task_id,
        count=len(payload),
        created_count=len(questions),
        updated_count=0,
    )


@router.patch(
    "/tasks/{task_id}/questions/{question_pk}",
    response_model=QuestionRead,
)
def update_teacher_question(
    task_id: int,
    question_pk: int,
    payload: QuestionUpdate,
    db: Session = Depends(get_db),
):
    question = db.scalar(
        select(Question).where(
            Question.task_id == task_id,
            Question.id == question_pk,
        )
    )
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    data = payload.model_dump(exclude_unset=True)
    if payload.options is not None:
        question.options_json = json.dumps(
            [opt.model_dump() for opt in payload.options],
            ensure_ascii=False,
        )
        data.pop("options", None)

    if payload.correct_answer is not None:
        question.correct_answer_json = json.dumps(payload.correct_answer, ensure_ascii=False)
        data.pop("correct_answer", None)

    if payload.accepted_answers is not None:
        question.accepted_answers_json = json.dumps(payload.accepted_answers, ensure_ascii=False)
        data.pop("accepted_answers", None)

    if payload.encouragement is not None:
        question.encouragement_json = json.dumps(
            payload.encouragement.model_dump(),
            ensure_ascii=False,
        )
        data.pop("encouragement", None)

    for key, value in data.items():
        setattr(question, key, value)

    db.commit()
    db.refresh(question)
    return _to_question_read(question)


@router.delete("/tasks/{task_id}/questions/{question_pk}")
def delete_teacher_question(
    task_id: int,
    question_pk: int,
    db: Session = Depends(get_db),
):
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

    try:
        submission_ids = select(Submission.id).where(Submission.task_id == task_id)
        db.execute(
            delete(SubmissionDetail).where(
                SubmissionDetail.submission_id.in_(submission_ids),
                SubmissionDetail.question_pk == question_pk,
            )
        )
        db.execute(
            delete(AnswerRecord).where(
                AnswerRecord.task_id == task_id,
                AnswerRecord.question_pk == question_pk,
            )
        )
        db.delete(question)
        db.commit()
    except Exception:
        db.rollback()
        raise

    return {
        "message": "Question deleted successfully",
        "task_id": task_id,
        "question_pk": question_pk,
    }


@router.post("/students/import", response_model=StudentImportResult)
def import_students(
    payload: list[StudentImportItem],
    db: Session = Depends(get_db),
):
    return _import_student_items(payload, db)


@router.post("/students/import-csv", response_model=StudentImportResult)
async def import_students_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only .csv files are supported")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="CSV file is empty")

    students = _parse_student_csv(content)
    return _import_student_items(students, db)


@router.get("/students", response_model=StudentListResponse)
def list_students(
    grade: str | None = Query(default=None),
    class_name: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    stmt = select(Student)

    if grade:
        stmt = stmt.where(Student.grade == grade)
    if class_name:
        stmt = stmt.where(Student.class_name == class_name)

    students = db.scalars(
        stmt.order_by(Student.grade.asc(), Student.class_name.asc(), Student.student_no.asc())
    ).all()

    return StudentListResponse(
        students=[StudentRead.model_validate(student) for student in students]
    )
