from typing import List, Literal

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator

from schemas.question import QuestionImportItem


QuestionType = Literal["judgment", "single_choice", "multiple_choice", "blank"]
DifficultyType = Literal["easy", "medium", "hard"]


class DifyOptionItem(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(validation_alias=AliasChoices("key", "id"))
    text: str
    explanation: str = ""


class DifyEncouragementItem(BaseModel):
    correct: str = ""
    wrong: str = ""
    retryCorrect: str = ""
    retryWrong: str = ""


class DifyQuestionImportItem(BaseModel):
    knowledge_point: str = ""
    question_type: QuestionType
    difficulty: DifficultyType = "medium"
    stem: str
    options: List[DifyOptionItem] = Field(default_factory=list)
    correct_answer: List[str] = Field(min_length=1)
    accepted_answers: List[str] = Field(default_factory=list)
    encouragement: DifyEncouragementItem = Field(default_factory=DifyEncouragementItem)
    student_explanation: str = ""
    score: int = 1

    @field_validator("stem")
    @classmethod
    def validate_stem(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("stem is required")
        return value

    def to_question_import_item(self) -> QuestionImportItem:
        return QuestionImportItem.model_validate(self.model_dump())


class DifyCreateTaskWithQuestionsRequest(BaseModel):
    title: str | None = None
    grade: str | None = None
    description: str = ""
    questions: List[DifyQuestionImportItem] = Field(min_length=1)

    @field_validator("title", "grade")
    @classmethod
    def validate_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return value
        value = value.strip()
        if not value:
            raise ValueError("field is required")
        return value


class DifyCreateTaskWithQuestionsResponse(BaseModel):
    success: bool
    task_id: int
    title: str
    grade: str
    question_count: int
    student_url: str
    teacher_analysis_url: str
    message: str
