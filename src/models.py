from pydantic import BaseModel, Field
from typing import List, Dict, Any
from enum import Enum

class HoldType(str, Enum):
    ALL = "all"
    HANDS = "hands"
    START = "start"
    FINISH = "finish"
    FOOT = "foot"

class HoldFrequency(BaseModel):
    x: int
    y: int
    frequency: int
    frequency_norm: float

class HeatmapRequest(BaseModel):
    min_grade: float = Field(ge=10, le=33)
    max_grade: float = Field(ge=10, le=33)
    angle: int = Field(ge=0, le=70, multiple_of=5)
    hold_type: HoldType = Field(default=HoldType.ALL)
    min_ascents: int = Field(default=10, ge=0)

class ResponseMetadata(BaseModel):
    min_grade: int
    max_grade: int
    angle: int
    hold_type: HoldType
    total_climbs: int
    invalid_climbs: int
    valid_climbs: int
    total_holds: int
    max_frequency: int

class HeatmapResponse(BaseModel):
    holds: List[HoldFrequency]
    metadata: ResponseMetadata