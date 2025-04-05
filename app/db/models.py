from datetime import datetime, date
from typing import Dict, List, Literal, Optional
from uuid import UUID, uuid4
from pydantic import EmailStr
from sqlmodel import  Float, SQLModel, Field, Relationship
from sqlalchemy import Column, Integer, String, Date, TIMESTAMP, Text, JSON, ForeignKey
from sqlalchemy.sql import func


class Clinician(SQLModel, table=True):
    __tablename__ = 'clinicians'
    
    clinician_id: UUID = Field(default_factory=uuid4, primary_key=True)
    first_name: str = Field(sa_column=Column(String(50), nullable=False)) 
    last_name: str = Field(sa_column=Column(String(50), nullable=False))
    specialty: Optional[str] = Field(sa_column=Column(String(100)))
    email: EmailStr = Field(sa_column=Column(String(100), unique=True, nullable=False))
    password: str = Field(sa_column=Column(String(100), nullable=False))
    created_at: Optional[datetime] = Field(sa_column=Column(TIMESTAMP, server_default=func.now()))
    updated_at: Optional[datetime] = Field(
        sa_column=Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    )
    # is_active: bool = Field(default=True)
    phone_number: Optional[str] = Field(sa_column=Column(String(15)))
    address: Optional[str] = Field(sa_column=Column(String(255)))

    patients: List["Patient"] = Relationship(back_populates="clinician")

class Patient(SQLModel, table=True):
    __tablename__ = 'patients'

    patient_id: UUID = Field(default_factory=uuid4, primary_key=True)
    first_name: str = Field(sa_column=Column(String(50), nullable=False))
    last_name: str = Field(sa_column=Column(String(50), nullable=False))
    date_of_birth: date = Field(sa_column=Column(Date, nullable=False))
    gender: Literal["male", "female", "other"] = Field(sa_column=Column(String(20)))
    adhd_subtype: Optional[str] = Field(sa_column=Column(String(30)))
    diagnosis_date: Optional[date] = Field(sa_column=Column(Date))
    medication_status: Optional[str] = Field(sa_column=Column(String(100)))
    parent_contact: Optional[str] = Field(sa_column=Column(String(100)))
    clinician_id: Optional[int] = Field(default=None, foreign_key="clinicians.clinician_id",nullable=True)  # Explicitly mark as nullable)
    notes: Optional[str] = Field(sa_column=Column(Text))
    email: str = Field(sa_column=Column(String(100), unique=True, nullable=False))
    password: Optional[str] = Field(sa_column=Column(String(100)))
    created_at: Optional[datetime] = Field(sa_column=Column(TIMESTAMP, server_default=func.now()))
    updated_at: Optional[datetime] = Field(
        sa_column=Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    )

    clinician: Optional[Clinician] = Relationship(back_populates="patients")
    sessions: List["Session"] = Relationship(back_populates="patient")

class Session(SQLModel, table=True):
    __tablename__ = 'sessions'
    
    session_id: UUID = Field(default_factory=uuid4, primary_key=True)
    session_date: datetime = Field(sa_column=Column(TIMESTAMP, nullable=False))
    session_duration: Optional[int] = Field(sa_column=Column(Integer))
    session_type: Optional[str] = Field(sa_column=Column(String(50)))
    notes: Optional[str] = Field(sa_column=Column(Text))
    created_at: Optional[datetime] = Field(sa_column=Column(TIMESTAMP, server_default=func.now()))
    
    patient_id: int = Field(foreign_key="patients.patient_id", nullable=False)
    patient: "Patient" = Relationship(back_populates="sessions")
    game_results: List["GameResult"] = Relationship(back_populates="session")


class GameResult(SQLModel, table=True):
    __tablename__ = 'game_results'
    
    result_id: UUID = Field(default_factory=uuid4, primary_key=True)
    game_type: str = Field(sa_column=Column(String(50), nullable=False))
    start_time: Optional[datetime] = Field(sa_column=Column(TIMESTAMP))
    end_time: Optional[datetime] = Field(sa_column=Column(TIMESTAMP))
    difficulty_level: Optional[int] = Field(sa_column=Column(Integer))
    created_at: Optional[datetime] = Field(sa_column=Column(TIMESTAMP, server_default=func.now()))
    session_id: int = Field(foreign_key="sessions.session_id", nullable=False)
    session: "Session" = Relationship(back_populates="game_results")

    crop_metrics: List["CropRecognitionMetrics"] = Relationship(back_populates="game_result")
    sequence_metrics: List["SequenceMemoryMetrics"] = Relationship(back_populates="game_result")
    matching_metrics: List["MatchingCardsMetrics"] = Relationship(back_populates="game_result")

class CropRecognitionMetrics(SQLModel, table=True):
    __tablename__ = 'crop_recognition_metrics'
    
    metric_id: UUID = Field(default_factory=uuid4, primary_key=True)
    result_id: int = Field(foreign_key="game_results.result_id")
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
    
    metric_id: UUID = Field(default_factory=uuid4, primary_key=True)
    result_id: int = Field(foreign_key="game_results.result_id")
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
    
    metric_id: UUID = Field(default_factory=uuid4, primary_key=True)
    result_id: int = Field(foreign_key="game_results.result_id")
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

    log_id: UUID = Field(default_factory=uuid4, primary_key=True)
    table_name: str = Field(sa_column=Column(String(50), nullable=False))
    operation: str = Field(sa_column=Column(String(10), nullable=False))
    record_id: int = Field(nullable=False)
    user_id: int = Field(nullable=False)
    timestamp: datetime = Field(sa_column=Column(TIMESTAMP, server_default=func.now()))
    old_data: Optional[dict] = Field(sa_column=Column(JSON))
    new_data: Optional[dict] = Field(sa_column=Column(JSON))