from typing import Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field


class PartCreatedPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    part_code: str = Field(min_length=1)
    quantity: int = Field(gt=0)
    warehouse: str = Field(min_length=1)


class IncomingEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_id: str = Field(min_length=1)
    source: str = Field(min_length=1)
    event_type: Literal["part.created"]
    occurred_at: AwareDatetime
    payload: PartCreatedPayload


class EventReceivedResponse(BaseModel):
    event_id: str
    status: Literal["received"]
