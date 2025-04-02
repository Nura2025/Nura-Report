from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models import Patient
from app.db.models import Patient
from app.db.database import get_db
from pydantic import BaseModel
from typing import Optional
from datetime import date

app = FastAPI()

class PatientCreate(BaseModel):
    first_name: str
    last_name: str
    date_of_birth: date
    gender: Optional[str] = None
    adhd_subtype: Optional[str] = None

@app.post("/patients/")
async def create_patient(
    patient: PatientCreate,
    db: AsyncSession = Depends(get_db)
):
    db_patient = Patient(**patient.dict())
    db.add(db_patient)
    await db.commit()
    await db.refresh(db_patient)
    return db_patient

@app.get("/patients/{patient_id}")
async def read_patient(
    patient_id: int,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Patient).where(Patient.patient_id == patient_id))
    patient = result.scalar_one_or_none()
    if patient is None:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient