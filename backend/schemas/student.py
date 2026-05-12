from datetime import datetime

from pydantic import BaseModel


class StudentImportItem(BaseModel):
    student_no: str
    student_name: str
    grade: str
    class_name: str
    status: str = "active"


class StudentRead(BaseModel):
    id: int
    student_no: str
    student_name: str
    grade: str
    class_name: str
    status: str

    model_config = {"from_attributes": True}


class StudentImportResult(BaseModel):
    message: str
    count: int
    created_count: int
    updated_count: int


class StudentListResponse(BaseModel):
    students: list[StudentRead]


class StudentTaskItem(BaseModel):
    task_id: int
    title: str
    grade: str
    question_count: int
    status: str
    student_task_status: str
    attempt_count: int
    answered_count: int
    correct_count: int
    accuracy: float
    progress: float
    last_submit_at: datetime | None


class StudentProfile(BaseModel):
    student_no: str
    student_name: str
    grade: str
    class_name: str
    status: str


class StudentTaskListResponse(BaseModel):
    student_id: str
    student: StudentProfile
    tasks: list[StudentTaskItem]


class StudentTaskAttemptSummary(BaseModel):
    session_id: str
    answered_count: int
    correct_count: int
    accuracy: float
    progress: float
    submitted_at: datetime


class StudentTaskQuestionResult(BaseModel):
    question_pk: int
    attempt_count: int
    first_is_correct: bool
    latest_is_correct: bool
    best_is_correct: bool


class StudentTaskSummaryResponse(BaseModel):
    task_id: int
    task_title: str
    student_no: str
    student_name: str
    question_count: int
    attempt_count: int
    latest_attempt: StudentTaskAttemptSummary | None
    best_accuracy: float
    history: list[StudentTaskAttemptSummary]
    question_results: list[StudentTaskQuestionResult]
