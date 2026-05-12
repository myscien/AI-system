from datetime import datetime

from pydantic import BaseModel

from core.time_utils import to_china_time


class TaskCreate(BaseModel):
    title: str
    grade: str


class TaskRead(TaskCreate):
    id: int
    question_count: int
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}

    @classmethod
    def model_validate(cls, obj, *args, **kwargs):
        result = super().model_validate(obj, *args, **kwargs)
        result.created_at = to_china_time(result.created_at)
        return result
