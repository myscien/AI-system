from pydantic import BaseModel


class QuestionAnalysisOption(BaseModel):
    id: str
    text: str
    explanation: str = ""


class QuestionOptionStat(BaseModel):
    option_id: str
    option_text: str
    count: int
    is_correct: bool


class QuestionAnalysisItem(BaseModel):
    question_id: int
    question_pk: int
    knowledge_point: str
    question_type: str
    difficulty: str
    stem: str
    options: list[QuestionAnalysisOption]
    correct_answer: list[str]
    total_answers: int
    correct_count: int
    wrong_count: int
    accuracy: float
    option_stats: list[QuestionOptionStat]


class StudentProgressItem(BaseModel):
    student_no: str
    student_name: str
    grade: str
    class_name: str
    answered_count: int
    correct_count: int
    accuracy: float
    progress: float
    status: str
    is_low_accuracy: bool


class TaskAnalysisResponse(BaseModel):
    task_id: int
    task_title: str
    total_students: int
    assigned_students: int
    submitted_students: int
    completed_students: int
    completion_rate: float
    average_accuracy: float
    low_accuracy_student_count: int
    question_stats: list[QuestionAnalysisItem]
    student_progress: list[StudentProgressItem]
    lowest_accuracy_questions: list[QuestionAnalysisItem]
