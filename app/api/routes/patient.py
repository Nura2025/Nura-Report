# app/routers/patients.py
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException , status
from sqlalchemy import select
from sqlmodel import Session
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependinces import get_current_clinician
from app.db.models import Clinician ,Patient
from app.schemas.auth_schema import PatientResponse
from app.db.database import get_session

router = APIRouter(tags=["Patients"])

@router.get("/{clinician_id}/patients", status_code=status.HTTP_200_OK)
async def get_all_patients_for_clinician(
    clinician_id: UUID,
    session: AsyncSession = Depends(get_session),
    # current_user: Clinician = Depends(get_current_clinician),  
):
    
    result = await session.execute(select(Clinician).where(Clinician.user_id == clinician_id))
    clinician = result.scalar_one_or_none()

    # if not clinician:
    #     raise HTTPException(
    #         status_code=status.HTTP_404_NOT_FOUND,
    #         detail="Clinician not found"
    #     )

    # Retrieve all patients associated with the clinician
    result = await session.execute(select(Patient).where(Patient.clinician_id == clinician_id))
    patients = result.scalars().all()

    # if not patients:
    #     raise HTTPException(
    #         status_code=status.HTTP_404_NOT_FOUND,
    #         detail="No patients found for this clinician"
    #     )

    return patients


@router.get("/{clinician_id}/patients/{patient_id}", status_code=status.HTTP_200_OK, response_model=PatientResponse)
async def get_patient_for_clinician(
    clinician_id: UUID,
    patient_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: Clinician = Depends(get_current_clinician),  
):
    """
    Retrieve a specific patient for a clinician.
    """
    if current_user.user_id != clinician_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this patient's data."
        )
    # Verify if the clinician exists
    result = await session.execute(select(Clinician).where(Clinician.user_id == clinician_id))
    clinician = result.scalar_one_or_none()

    if not clinician:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Clinician not found"
        )

    # Retrieve the patient associated with the clinician
    result = await session.execute(
        select(Patient).where(Patient.user_id == patient_id, Patient.clinician_id == clinician_id)
    )
    patient = result.scalar_one_or_none()

    if not patient:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found or not associated with this clinician"
        )

    return patient
# @router.patch("/me", response_model=Patient)
# async def update_patient_profile(
#     update_data: PatientUpdate,
#     current_user: Patient = Depends(require_role("patient")),
#     session: Session = Depends(get_session)
# ):
#     for key, value in update_data.dict(exclude_unset=True).items():
#         setattr(current_user, key, value)
#     session.add(current_user)
#     session.commit()
#     session.refresh(current_user)
#     return current_user

# @router.patch("/{patient_id}", response_model=Patient)
# async def update_patient_by_clinician(
#     patient_id: int,
#     update_data: PatientUpdate,
#     current_user: Clinician = Depends(require_role("clinician")),
#     session: Session = Depends(get_session)
# ):
#     patient = session.get(Patient, patient_id)
#     if not patient:
#         raise HTTPException(status_code=404, detail="Patient not found")
    
#     if patient.clinician_id != current_user.clinician_id:
#         raise HTTPException(status_code=403, detail="Not authorized to update this patient")
    
#     for key, value in update_data.dict(exclude_unset=True).items():
#         setattr(patient, key, value)
    
#     session.add(patient)
#     session.commit()
#     session.refresh(patient)
#     return patient