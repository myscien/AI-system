from typing import List, Literal
from pydantic import BaseModel


QuestionType = Literal["judgment", "single_choice", "multiple_choice", "blank"]
DifficultyType = Literal["easy", "medium", "hard"]


class OptionItem(BaseModel):
    id: str
    text: str
    explanation: str


class EncouragementItem(BaseModel):
    correct: str
    wrong: str
    retryCorrect: str
    retryWrong: str


class QuestionImportItem(BaseModel):
    knowledge_point: str
    question_type: QuestionType
    difficulty: DifficultyType
    stem: str
    options: List[OptionItem]
    correct_answer: List[str]
    accepted_answers: List[str]
    encouragement: EncouragementItem
    student_explanation: str
    score: int


class QuestionUpdate(BaseModel):
    knowledge_point: str | None = None
    question_type: QuestionType | None = None
    difficulty: DifficultyType | None = None
    stem: str | None = None
    options: List[OptionItem] | None = None
    correct_answer: List[str] | None = None
    accepted_answers: List[str] | None = None
    encouragement: EncouragementItem | None = None
    student_explanation: str | None = None
    score: int | None = None


class QuestionRead(BaseModel):
    question_pk: int
    knowledge_point: str
    question_type: QuestionType
    difficulty: DifficultyType
    stem: str
    options: List[OptionItem]
    correct_answer: List[str]
    accepted_answers: List[str]
    encouragement: EncouragementItem
    student_explanation: str
    score: int

    model_config = {"from_attributes": True}
