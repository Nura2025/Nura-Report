# models.py
from datetime import datetime, date
from typing import Dict, List, Literal, Optional
from uuid import UUID, uuid4
from pydantic import EmailStr, root_validator
from sqlmodel import  Float, SQLModel, Field, Relationship, text
from sqlalchemy import Column, Integer, PrimaryKeyConstraint, String, Date, TIMESTAMP, Text, JSON, Enum
from sqlalchemy.sql import func
from sqlalchemy import Enum as SQLAlchemyEnum
from enum import Enum

from app.db.enums import GameType


class CaseInsensitiveEnum(str, Enum):
    @classmethod
    def _missing_(cls, value):
        value = value.lower()
        for member in cls:
            if member.lower() == value:
                return member
        return None
    
class UserRole(CaseInsensitiveEnum):
    DOCTOR = "doctor"
    PATIENT = "patient"
    ADMIN = "admin"

class UserBase(SQLModel):
    email: EmailStr = Field(sa_column=Column(String(100), unique=True, nullable=False))
    username: str = Field(sa_column=Column(String(50), nullable=False , unique=True))
    role: str = Field(sa_column=Column(String(50), nullable=False))
    is_active: bool = Field(default=True)
    created_at: Optional[datetime] = Field(
        sa_column=Column(TIMESTAMP, server_default=func.now())
    )
    updated_at: Optional[datetime] = Field(
        sa_column=Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    )

class User(UserBase, table=True):
    __tablename__ = 'users'
    
    user_id: UUID = Field(default_factory=uuid4, primary_key=True)
    hashed_password: str = Field(sa_column=Column(String(255), nullable=False))
    
    # Relationships
    clinician: Optional["Clinician"] = Relationship(back_populates="user",
                                                     sa_relationship_kwargs={"cascade": "all, delete-orphan", 
                                                                        "uselist": False,
                                                                        "single_parent": True}
)
    patient: Optional["Patient"] = Relationship(back_populates="user",
                                                sa_relationship_kwargs={"cascade": "all, delete-orphan", 
                                                                        "uselist": False,
                                                                        "single_parent": True}
                                              )

class Clinician(SQLModel, table=True):
    __tablename__ = 'clinicians'
    
    user_id: UUID = Field(foreign_key="users.user_id", primary_key=True)
    
    first_name: str = Field(sa_column=Column(String(50), nullable=False))
    last_name: str = Field(sa_column=Column(String(50), nullable=False))
    specialty: Optional[str] = Field(sa_column=Column(String(100)))
    phone_number: Optional[str] = Field(sa_column=Column(String(15)))
    address: Optional[str] = Field(sa_column=Column(String(255)))
    created_at: Optional[datetime] = Field(
        sa_column=Column(TIMESTAMP, server_default=func.now())
    )
    updated_at: Optional[datetime] = Field(
        sa_column=Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    )
    
    # Relationships
    user: User = Relationship(back_populates="clinician")
    patients: List["Patient"] = Relationship( back_populates="clinician")

class Patient(SQLModel, table=True):
    __tablename__ = 'patients'
    
    user_id: UUID = Field(foreign_key="users.user_id", primary_key=True)
    clinician_id: Optional[UUID] = Field(default=None, foreign_key="clinicians.user_id")
    
    first_name: str = Field(sa_column=Column(String(50)))
    last_name: str = Field(sa_column=Column(String(50)))
    date_of_birth: date = Field(sa_column=Column(Date))
    gender: Literal["male", "female", "other"] = Field(sa_column=Column(String(20)))
    adhd_subtype: Optional[str] = Field(sa_column=Column(String(30)))
    diagnosis_date: Optional[date] = Field(sa_column=Column(Date))
    medication_status: Optional[str] = Field(sa_column=Column(String(100)))
    parent_contact: Optional[str] = Field(sa_column=Column(String(100)))
    notes: Optional[str] = Field(sa_column=Column(Text))
    phone_number: Optional[str] = Field(sa_column=Column(String(15)))
    address: Optional[str] = Field(sa_column=Column(String(255)))
    created_at: Optional[datetime] = Field(
        sa_column=Column(TIMESTAMP, server_default=func.now())
    )
    updated_at: Optional[datetime] = Field(
        sa_column=Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    )
    # Relationships
    user: User = Relationship(back_populates="patient")
    clinician: Optional[Clinician] = Relationship(back_populates="patients")
    sessions: List["Session"] = Relationship(back_populates="patient")


    
class Session(SQLModel, table=True):
    __tablename__ = 'sessions'
    
    session_id: UUID = Field( default_factory=uuid4,primary_key=True,sa_column_kwargs={"server_default": text("gen_random_uuid()")})  
    session_date: datetime = Field(sa_column=Column(TIMESTAMP, nullable=False))
    session_duration: Optional[int] = Field(sa_column=Column(Integer))
    notes: Optional[str] = Field(sa_column=Column(Text))
    created_at: Optional[datetime] = Field(sa_column=Column(TIMESTAMP(timezone=False), server_default=func.now() , nullable=False))
    
    user_id: UUID = Field(foreign_key="patients.user_id", nullable=False)
    patient: "Patient" = Relationship(back_populates="sessions")
    game_results: List["GameResult"] = Relationship(back_populates="session",
                                                    sa_relationship_kwargs={"cascade": "all, delete-orphan"}
)


class GameResult(SQLModel, table=True):
    __tablename__ = 'game_results'
    
    result_id: UUID = Field( default_factory=uuid4,primary_key=True,sa_column_kwargs={"server_default": text("gen_random_uuid()")})  
    game_type: GameType = Field(sa_column=Column(SQLAlchemyEnum(GameType), nullable=False))
    start_time: Optional[datetime] = Field(sa_column=Column(TIMESTAMP))
    end_time: Optional[datetime] = Field(sa_column=Column(TIMESTAMP))
    difficulty_level: Optional[int] = Field(sa_column=Column(Integer))
    created_at: Optional[datetime] = Field(sa_column=Column(TIMESTAMP, server_default=func.now()))
    session_id: UUID = Field(foreign_key="sessions.session_id", nullable=False)

    session: "Session" = Relationship(back_populates="game_results")
    crop_metrics: Optional["CropRecognitionMetrics"] = Relationship(back_populates="game_result", 
                                                                    sa_relationship_kwargs={"cascade": "all, delete-orphan"}
)
    sequence_metrics: Optional["SequenceMemoryMetrics"] = Relationship(back_populates="game_result",
                                                                        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
)
    matching_metrics: Optional["MatchingCardsMetrics"] = Relationship(back_populates="game_result",
                                                                     sa_relationship_kwargs={"cascade": "all, delete-orphan"}
)

class CropRecognitionMetrics(SQLModel, table=True):
    __tablename__ = 'crop_recognition_metrics'
    
    metric_id:UUID = Field( default_factory=uuid4,primary_key=True,sa_column_kwargs={"server_default": text("gen_random_uuid()")})  
    result_id: UUID = Field(foreign_key="game_results.result_id")
    crops_identified: int
    omission_errors: int
    response_times: Dict[str, float] = Field(sa_column=Column(JSON))
    distractions: int
    total_crops_presented: int
    created_at: datetime = Field(
        sa_column=Column(TIMESTAMP(timezone=True), server_default=func.now())
    )
    score: Optional[float] = Field(sa_column=Column(Float))
    
    game_result: GameResult = Relationship(back_populates="crop_metrics")

class SequenceMemoryMetrics(SQLModel, table=True):
    __tablename__ = 'sequence_memory_metrics'
    
    metric_id: UUID = Field( default_factory=uuid4,primary_key=True,sa_column_kwargs={"server_default": text("gen_random_uuid()")})  
    result_id: UUID = Field(foreign_key="game_results.result_id")
    sequence_length: int
    commission_errors: int
    num_of_trials: int
    retention_times: List[int] = Field(sa_column=Column(JSON))
    total_sequence_elements: int
    created_at: datetime = Field(
    sa_column=Column(TIMESTAMP(timezone=True), server_default=func.now())
       )
    score: Optional[float] = Field(sa_column=Column(Float))

    game_result: GameResult = Relationship(back_populates="sequence_metrics")



class MatchingCardsMetrics(SQLModel, table=True):
    __tablename__ = 'matching_cards_metrics'
    
    metric_id: UUID = Field( default_factory=uuid4,primary_key=True,sa_column_kwargs={"server_default": text("gen_random_uuid()")})  
    result_id: UUID = Field(foreign_key="game_results.result_id")
    matches_attempted: int
    correct_matches: int
    incorrect_matches: int
    time_per_match: List[int] = Field(sa_column=Column(JSON))
    created_at: datetime = Field(
    sa_column=Column(TIMESTAMP(timezone=True), server_default=func.now())
       )
    score: Optional[float] = Field(sa_column=Column(Float))

    game_result: GameResult = Relationship(back_populates="matching_metrics")

class AuditLog(SQLModel, table=True):
    __tablename__ = 'audit_log'

    log_id: UUID = Field( default_factory=uuid4,primary_key=True,sa_column_kwargs={"server_default": text("gen_random_uuid()")})  
    table_name: str = Field(sa_column=Column(String(50), nullable=False))
    operation: str = Field(sa_column=Column(String(10), nullable=False))
    record_id: int = Field(nullable=False)
    user_id: UUID = Field(nullable=False)
    timestamp: datetime = Field(sa_column=Column(TIMESTAMP, server_default=func.now()))
    old_data: Optional[dict] = Field(sa_column=Column(JSON))
    new_data: Optional[dict] = Field(sa_column=Column(JSON))

class AttentionAnalysis(SQLModel, table=True):
    __tablename__ = "attention_analysis"
    __table_args__ = (
        PrimaryKeyConstraint("analysis_id", "created_at"),
        {"extend_existing": True}
    )

    analysis_id:UUID = Field( default_factory=uuid4,primary_key=True,sa_column_kwargs={"server_default": text("gen_random_uuid()")})  
    
    created_at: datetime = Field(
        sa_column=Column(
            TIMESTAMP(timezone=True),
            server_default=func.now()
        )
    )
    session_id: UUID = Field(foreign_key="sessions.session_id")
    crop_score: float
    sequence_score: float
    overall_score: float
    percentile: float = Field(default=50.0)
    classification: str = Field(default="Average")

class MemoryAnalysis(SQLModel, table=True):
    __tablename__ = "memory_analysis"
    __table_args__ = (
        PrimaryKeyConstraint("analysis_id", "created_at"),
        {"extend_existing": True}
    )

    analysis_id: UUID = Field(default_factory=uuid4, primary_key=True, sa_column_kwargs={"server_default": text("gen_random_uuid()")})
    session_id: UUID = Field(foreign_key="sessions.session_id")
    
    overall_memory_score: float
    working_memory_score: float
    visual_memory_score: float
    data_completeness: float = Field(default=0.5)  # 0.5 = one game, 1.0 = both games
    tasks_used: List[str] = Field(sa_column=Column(JSON), default=[])
    percentile: float = Field(default=50.0)
    classification: str = Field(default="Average")
    working_memory_components: Dict[str, float] = Field(sa_column=Column(JSON), default={})
    visual_memory_components: Dict[str, float] = Field(sa_column=Column(JSON), default={})
    
    created_at: datetime = Field(
        sa_column=Column(
            TIMESTAMP(timezone=True),
            server_default=func.now()
        )
    )

class ImpulseAnalysis(SQLModel, table=True):
    __tablename__ = "impulse_analysis"
    __table_args__ = (
        PrimaryKeyConstraint("analysis_id", "created_at"),
        {"extend_existing": True}
    )

    analysis_id: UUID = Field(default_factory=uuid4, primary_key=True, sa_column_kwargs={"server_default": text("gen_random_uuid()")})
    session_id: UUID = Field(foreign_key="sessions.session_id")
    overall_impulse_control_score: float
    inhibitory_control: float
    response_control: float
    decision_speed: float
    error_adaptation: float
    data_completeness: float = Field(default=0.33)  # Fraction of games used
    games_used: List[str] = Field(sa_column=Column(JSON), default=[])
    percentile: float = Field(default=50.0)
    classification: str = Field(default="Average")
    
    created_at: datetime = Field(
        sa_column=Column(
            TIMESTAMP(timezone=True),
            server_default=func.now()
        )
    )
class ExecutiveFunctionAnalysis(SQLModel, table=True):
    __tablename__ = "executive_function_analysis"
    __table_args__ = (
        PrimaryKeyConstraint("analysis_id", "created_at"),
        {"extend_existing": True}
    )

    analysis_id: UUID = Field(default_factory=uuid4, primary_key=True, sa_column_kwargs={"server_default": text("gen_random_uuid()")})
    session_id: UUID = Field(foreign_key="sessions.session_id")
    executive_function_score: float
    
    # Component contributions
    memory_contribution: float
    impulse_contribution: float
    attention_contribution: float
    percentile: float = Field(default=50.0)
    classification: str = Field(default="Average")
    profile_pattern: str = Field(default="Mixed executive function profile")
    created_at: datetime = Field(
        sa_column=Column(
            TIMESTAMP(timezone=True),
            server_default=func.now()
        )
    )

class NormativeData(SQLModel, table=True):
    __tablename__ = "normative_data"

    id: UUID = Field(default_factory=uuid4, primary_key=True, sa_column_kwargs={"server_default": text("gen_random_uuid()")})
    domain: str  # "memory", "impulse_control", "executive_function", "attention"
    age_group: str  # "5-7", "8-10", "11-13", "14-16", "adult"
    mean_score: float
    standard_deviation: float
    sample_size: int = Field(default=100)
    reference: str  # Scientific reference
    clinical_group: Optional[str] = Field(default=None)  # "ADHD" or None for typical development
    reliability: float = Field(default=0.85)
    created_at: datetime = Field(
        sa_column=Column(
            TIMESTAMP(timezone=True),
            server_default=func.now()
        )
    )