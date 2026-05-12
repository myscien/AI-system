from pydantic import BaseModel


class TeachingSummaryTask(BaseModel):
    task_id: int
    task_title: str
    grade: str
    class_name: str | None


class TeachingSummaryOverview(BaseModel):
    assigned_students: int
    submitted_students: int
    not_started_students: int
    completed_students: int
    completion_rate: float
    average_accuracy: float
    low_accuracy_student_count: int


class TeachingSummaryOption(BaseModel):
    id: str
    text: str
    is_correct: bool
    selected_count: int


class TeachingSummaryWrongOption(BaseModel):
    option_id: str
    option_text: str
    count: int


class TeachingSummaryWeakQuestion(BaseModel):
    question_id: int
    question_pk: int
    knowledge_point: str
    question_type: str
    difficulty: str
    stem: str
    options: list[TeachingSummaryOption]
    correct_answer: list[str]
    total_answers: int
    correct_count: int
    wrong_count: int
    accuracy: float
    top_wrong_options: list[TeachingSummaryWrongOption]


class TeachingSummaryKnowledgePoint(BaseModel):
    knowledge_point: str
    question_count: int
    average_accuracy: float
    weak_question_count: int


class TeachingSummaryStudent(BaseModel):
    student_no: str
    student_name: str
    grade: str
    class_name: str
    answered_count: int
    correct_count: int
    accuracy: float
    progress: float
    status: str


class TeachingSummaryStudentGroups(BaseModel):
    not_started: list[TeachingSummaryStudent]
    in_progress: list[TeachingSummaryStudent]
    low_accuracy: list[TeachingSummaryStudent]
    high_accuracy: list[TeachingSummaryStudent]


class TeachingSummaryResponse(BaseModel):
    task: TeachingSummaryTask
    overview: TeachingSummaryOverview
    weak_questions: list[TeachingSummaryWeakQuestion]
    knowledge_points: list[TeachingSummaryKnowledgePoint]
    student_groups: TeachingSummaryStudentGroups
    copy_text: str
