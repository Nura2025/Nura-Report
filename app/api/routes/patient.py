# # app/routers/patients.py
# from fastapi import APIRouter, Depends, HTTPException
# from sqlmodel import Session

# from app.db.models import Clinician ,Patient
# from app.utils.security import get_current_user, require_role
# from app.db.database import get_session
# from app.schemas.patient_schema import PatientUpdate

# router = APIRouter()

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