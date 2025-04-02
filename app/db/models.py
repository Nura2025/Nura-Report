from sqlalchemy import Column, Integer, String, Date, TIMESTAMP, Text, JSON
from sqlalchemy.sql import func
from app.db.database import Base

class Patient(Base):
    __tablename__ = 'patients'
    
    patient_id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    date_of_birth = Column(Date, nullable=False)
    gender = Column(String(20))
    adhd_subtype = Column(String(30))
    diagnosis_date = Column(Date)
    medication_status = Column(String(100))
    parent_contact = Column(String(100))
    clinician_id = Column(Integer)
    notes = Column(Text)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

class Clinician(Base):
    __tablename__ = 'clinicians'
    
    clinician_id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    specialty = Column(String(100))
    email = Column(String(100), unique=True)
    created_at = Column(TIMESTAMP, server_default=func.now())

class Session(Base):
    __tablename__ = 'sessions'
    
    session_id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer)
    session_date = Column(TIMESTAMP, nullable=False)
    session_duration = Column(Integer)
    clinician_id = Column(Integer)
    session_type = Column(String(50))
    notes = Column(Text)
    created_at = Column(TIMESTAMP, server_default=func.now())

class GameResult(Base):
    __tablename__ = 'game_results'
    
    result_id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer)
    game_type = Column(String(50), nullable=False)
    start_time = Column(TIMESTAMP)
    end_time = Column(TIMESTAMP)
    difficulty_level = Column(Integer)
    created_at = Column(TIMESTAMP, server_default=func.now())

class MatchingCardsMetrics(Base):
    __tablename__ = 'matching_cards_metrics'
    
    metric_id = Column(Integer, primary_key=True, index=True)
    result_id = Column(Integer)
    matches_attempted = Column(Integer)
    correct_matches = Column(Integer)
    incorrect_matches = Column(Integer)
    time_per_match = Column(JSON)
    session_duration = Column(Integer)
    created_at = Column(TIMESTAMP, server_default=func.now())

class CropRecognitionMetrics(Base):
    __tablename__ = 'crop_recognition_metrics'
    
    metric_id = Column(Integer, primary_key=True, index=True)
    result_id = Column(Integer)
    crops_identified = Column(Integer)
    omission_errors = Column(Integer)
    response_times = Column(JSON)
    distractions = Column(Integer)
    total_crops_presented = Column(Integer)
    created_at = Column(TIMESTAMP, server_default=func.now())

class SequenceMemoryMetrics(Base):
    __tablename__ = 'sequence_memory_metrics'
    
    metric_id = Column(Integer, primary_key=True, index=True)
    result_id = Column(Integer)
    sequence_length = Column(Integer)
    commission_errors = Column(Integer)
    num_of_trials = Column(Integer)
    retention_times = Column(JSON)
    total_sequence_elements = Column(Integer)
    created_at = Column(TIMESTAMP, server_default=func.now())

class AuditLog(Base):
    __tablename__ = 'audit_log'
    
    log_id = Column(Integer, primary_key=True, index=True)
    table_name = Column(String(50), nullable=False)
    operation = Column(String(10), nullable=False)
    record_id = Column(Integer, nullable=False)
    user_id = Column(Integer, nullable=False)
    timestamp = Column(TIMESTAMP, server_default=func.now())
    old_data = Column(JSON)
    new_data = Column(JSON)