from datetime import datetime

from pydantic import BaseModel

from core.time_utils import to_china_time


class TeacherTaskCreate(BaseModel):
    title: str
    grade: str
    description: str = ""


class TeacherTaskUpdate(BaseModel):
    title: str | None = None
    grade: str | None = None
    description: str | None = None
    status: str | None = None


class TeacherTaskRead(BaseModel):
    id: int
    title: str
    grade: str
    description: str
    question_count: int
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}

    @classmethod
    def model_validate(cls, obj, *args, **kwargs):
        result = super().model_validate(obj, *args, **kwargs)
        result.created_at = to_china_time(result.created_at)
        return result


class TeacherQuestionImportResult(BaseModel):
    message: str
    task_id: int
    count: int
    created_count: int
    updated_count: int
