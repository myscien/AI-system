from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from core.database import get_db
from models.student import Student
from models.task import Task
from schemas.student import StudentProfile, StudentTaskListResponse, StudentTaskSummaryResponse
from services.student_learning import build_student_task_list, build_student_task_summary

router = APIRouter()


@router.get("/tasks", response_model=StudentTaskListResponse)
def list_student_tasks(
    student_id: str = Query(..., description="8-digit student ID"),
    db: Session = Depends(get_db),
):
    if not (len(student_id) == 8 and student_id.isdigit()):
        raise HTTPException(status_code=400, detail="student_id must be an 8-digit number")

    student = db.scalar(
        select(Student).where(
            Student.student_no == student_id,
            Student.status == "active",
        )
    )
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    tasks = db.scalars(
        select(Task)
        .options(selectinload(Task.questions))
        .where(Task.grade == student.grade)
        .order_by(Task.id.desc())
    ).all()

    return StudentTaskListResponse(
        student_id=student_id,
        student=StudentProfile(
            student_no=student.student_no,
            student_name=student.student_name,
            grade=student.grade,
            class_name=student.class_name,
            status=student.status,
        ),
        tasks=build_student_task_list(student, tasks, db),
    )


@router.get("/tasks/{task_id}/summary", response_model=StudentTaskSummaryResponse)
def get_student_task_summary(
    task_id: int,
    student_id: str = Query(..., description="8-digit student ID"),
    db: Session = Depends(get_db),
):
    if not (len(student_id) == 8 and student_id.isdigit()):
        raise HTTPException(status_code=400, detail="student_id must be an 8-digit number")

    student = db.scalar(
        select(Student).where(
            Student.student_no == student_id,
            Student.status == "active",
        )
    )
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    task = db.scalar(
        select(Task)
        .options(selectinload(Task.questions))
        .where(
            Task.id == task_id,
            Task.grade == student.grade,
        )
    )
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return build_student_task_summary(student, task, db)
