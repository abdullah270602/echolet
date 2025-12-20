from pydantic import BaseModel


class UsageStatus(BaseModel):
    remaining_seconds: int
    used_seconds: int
    limit_seconds: int


class UsageRecordRequest(BaseModel):
    talk_seconds: int
