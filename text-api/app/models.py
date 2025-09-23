from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Literal, Union, Dict
from datetime import datetime
import uuid

class TextCreate(BaseModel):
    session_id: Optional[str] = None
    cefr_level: str
    text_id: str
    text_translated: str
    
    @field_validator('cefr_level')
    @classmethod
    def validate_cefr_level(cls, v):
        valid_levels = ["A1", "A2", "B1"]
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f'CEFR level must be one of {valid_levels}')
        return v_upper

class TextUpdate(BaseModel):
    text_translated: str

class Text(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    cefr_level: str
    text_id: str
    text_translated: str
    version: int = 1
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    metrics_meaningbert: Optional[float] = None
    metrics_cefr_compliance: Optional[str] = None
    
    @field_validator('cefr_level')
    @classmethod
    def validate_cefr_level(cls, v):
        valid_levels = ["A1", "A2", "B1"]
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f'CEFR level must be one of {valid_levels}')
        return v_upper

class MetricsEvaluation(BaseModel):
    cefr_compliance: str
    bertscore: float
    meaningbert: float
    
    @field_validator('cefr_compliance')
    @classmethod
    def validate_cefr(cls, v):
        valid_levels = ["A1", "A2", "B1", "B2", "C1", "C2"]
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f'CEFR compliance must be one of {valid_levels}')
        return v_upper

class FeedbackCreate(BaseModel):
    session_id: str
    approval: str
    grade: Union[int, str]
    feedback: str
    cefr_compliance: Optional[str] = None
    bertscore: Optional[float] = None
    meaningbert: Optional[float] = None
    
    @field_validator('cefr_compliance')
    @classmethod
    def validate_cefr(cls, v):
        if v is None:
            return v
        valid_levels = ["A1", "A2", "B1", "B2", "C1", "C2"]
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f'CEFR compliance must be one of {valid_levels}')
        return v_upper
    
    @field_validator('approval')
    @classmethod
    def validate_approval(cls, v):
        valid_approvals = ["PASS", "FAIL"]
        v_upper = v.upper()
        if v_upper not in valid_approvals:
            raise ValueError(f'Approval must be one of {valid_approvals}')
        return v_upper
    
    @field_validator('grade')
    @classmethod
    def validate_grade(cls, v):
        try:
            grade_int = int(v)
            if grade_int < 1 or grade_int > 10:
                raise ValueError('Grade must be between 1 and 10')
            return grade_int
        except (ValueError, TypeError):
            raise ValueError('Grade must be a number between 1 and 10')

class Feedback(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    approval: str
    grade: int
    feedback: str
    metrics: Optional[MetricsEvaluation] = None
    created_at: datetime = Field(default_factory=datetime.now)
    
    @field_validator('approval')
    @classmethod
    def validate_approval(cls, v):
        valid_approvals = ["PASS", "FAIL"]
        v_upper = v.upper()
        if v_upper not in valid_approvals:
            raise ValueError(f'Approval must be one of {valid_approvals}')
        return v_upper

class CurrentState(BaseModel):
    text: Text
    feedback: Optional[Feedback] = None
    attempt_number: int = 1
    best_attempt: Optional[Text] = None

class LLMMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Optional[dict] = None

class History(BaseModel):
    session_id: str
    created_at: datetime
    messages: List[LLMMessage]

class SessionCreate(BaseModel):
    target_cefr: str
    
    @field_validator('target_cefr')
    @classmethod
    def validate_target_cefr(cls, v):
        valid_levels = ["A1", "A2", "B1", "B2", "C1", "C2"]
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f'Target CEFR level must be one of {valid_levels}')
        return v_upper

class SessionResponse(BaseModel):
    session_id: str
    created_at: datetime
    target_cefr: str

class TaggedWord(BaseModel):
    word: str
    tagged_as: str
    level: str

class TextTagRequest(BaseModel):
    text: str

class TextTagResponse(BaseModel):
    text: str
    tagged_words: Dict[str, List[str]]  # {level: [words]}
    stats: dict