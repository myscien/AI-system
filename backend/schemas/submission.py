from typing import List
from pydantic import BaseModel


class StudentAnswerItem(BaseModel):
    question_pk: int
    student_answer: List[str]


class SubmissionCreate(BaseModel):
    student_name: str
    student_no: str
    answers: List[StudentAnswerItem]


class SubmissionQuestionResult(BaseModel):
    question_pk: int
    student_answer: List[str]
    correct_answer: List[str]
    is_correct: bool
    score_awarded: int
    selected_option_explanation: str
    student_explanation: str


class SubmissionResult(BaseModel):
    task_id: int
    student_name: str
    student_no: str
    total_score: int
    results: List[SubmissionQuestionResult]


class SingleQuestionSubmissionCreate(BaseModel):
    student_name: str = ""
    student_no: str
    student_answer: List[str]
    session_id: str


class SingleQuestionSubmissionResult(BaseModel):
    task_id: int
    question_pk: int
    student_name: str
    student_no: str
    student_answer: List[str]
    correct_answer: List[str]
    is_correct: bool
    score_awarded: int
    saved: bool
    message: str
    selected_option_explanation: str
    student_explanation: str
