from fastapi import FastAPI
from core.database import Base, engine, ensure_sqlite_schema_compatibility
from fastapi.middleware.cors import CORSMiddleware
from models.answer_record import AnswerRecord
from models.task import Task
from models.question import Question
from models.student import Student
from models.submission import Submission
from models.submission_detail import SubmissionDetail

from api.teacher_routes import router as teacher_router
from api.task_routes import router as task_router
from api.question_routes import router as question_router
from api.submission_routes import router as submission_router
from api.student_routes import router as student_router
from api.dify_routes import router as dify_router

app = FastAPI(title="课堂答题平台原型")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ensure_sqlite_schema_compatibility()
Base.metadata.create_all(bind=engine)

app.include_router(teacher_router, prefix="/api/teacher", tags=["teacher"])
app.include_router(task_router, prefix="/api/tasks", tags=["tasks"])
app.include_router(question_router, prefix="/api/tasks", tags=["questions"])
app.include_router(submission_router, prefix="/api/tasks", tags=["submissions"])
app.include_router(student_router, prefix="/api/student", tags=["student"])
app.include_router(dify_router, prefix="/api/dify", tags=["Dify"])
