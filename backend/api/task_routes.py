from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from core.database import get_db
from models.task import Task
from schemas.analysis import TaskAnalysisResponse
from schemas.task import TaskCreate, TaskRead
from schemas.teaching_summary import TeachingSummaryResponse
from services.analysis import build_task_analysis
from services.teaching_summary import build_teaching_summary

router = APIRouter()


def _normalize_grade(grade: str) -> str:
    return grade.strip().removesuffix("\u5e74\u7ea7")


@router.post("", response_model=TaskRead)
def create_task(payload: TaskCreate, db: Session = Depends(get_db)):
    task_data = payload.model_dump()
    task_data["grade"] = _normalize_grade(task_data["grade"])
    task = Task(**task_data)
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@router.get("/{task_id}", response_model=TaskRead)
def get_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(Task).options(selectinload(Task.questions)).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.get("", response_model=list[TaskRead])
def list_tasks(db: Session = Depends(get_db)):
    tasks = db.scalars(
        select(Task)
        .options(selectinload(Task.questions))
        .order_by(Task.id.desc())
    ).all()
    return tasks


@router.get("/{task_id}/analysis", response_model=TaskAnalysisResponse)
def get_task_analysis(
    task_id: int,
    grade: str | None = Query(default=None),
    class_name: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return build_task_analysis(
        task_id=task_id,
        db=db,
        grade=grade,
        class_name=class_name,
    )


@router.get("/{task_id}/teaching-summary", response_model=TeachingSummaryResponse)
def get_teaching_summary(
    task_id: int,
    grade: str | None = Query(default=None),
    class_name: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    task = db.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    analysis = build_task_analysis(
        task_id=task_id,
        db=db,
        grade=grade,
        class_name=class_name,
    )
    return build_teaching_summary(
        analysis=analysis,
        grade=grade or task.grade,
        class_name=class_name,
    )
