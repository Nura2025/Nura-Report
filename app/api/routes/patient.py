# app/routers/patients.py
from datetime import datetime, timedelta
import secrets
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException , status
from pydantic import EmailStr
from sqlalchemy import select
from sqlmodel import Session
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependinces import get_current_clinician, get_current_patient, get_current_user
from app.db.models import Clinician ,Patient, User
from app.schemas.auth_schema import PatientResponse
from app.db.database import get_session
from app.schemas.user_schema import UserUpdateByEmail

router = APIRouter(tags=["Patients"])

from datetime import datetime, timedelta
import secrets
from app.db.models import InvitationToken

@router.post("/generate-invitation-link", status_code=status.HTTP_200_OK)
async def generate_invitation_link(
    patient_email: EmailStr,
    current_clinician: Clinician = Depends(get_current_clinician),
    session: AsyncSession = Depends(get_session),
):
    """
    Generate a unique invitation link for the clinician to share with a patient.
    """
    # Generate a secure token
    token = secrets.token_urlsafe(32)
    expiration = datetime.utcnow() + timedelta(hours=24)  # Token expires in 24 hours

    # Save the token in the database
    invitation = InvitationToken(
        token=token,
        clinician_id=current_clinician.user_id,
        patient_email=patient_email,  # Include patient_email

        expires_at=expiration,
        used=False,
    )
    session.add(invitation)
    await session.commit()

    # Generate the invitation link
    invitation_link = f"http://127.0.0.1:8000/accept-invitation?token={token}"
    return {"invitation_link": invitation_link}

@router.patch("/update-user-by-email")
async def update_user_by_email(
    update_data: UserUpdateByEmail,
    session: AsyncSession = Depends(get_session),
):
    # Fetch the user
    result = await session.execute(select(User).where(User.email == update_data.email))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Update allowed fields in User
    if update_data.username:
        user.username = update_data.username
    session.add(user)

    # Check if patient exists for this user
    result = await session.execute(select(Patient).where(Patient.user_id == user.user_id))
    patient = result.scalar_one_or_none()

    if patient:
        # Update allowed fields in Patient
        for field in ["first_name", "last_name", "gender", "date_of_birth", "phone_number"]:
            value = getattr(update_data, field)
            if value is not None:
                setattr(patient, field, value)
        session.add(patient)

    await session.commit()
    return {"message": "User and patient profile updated successfully"}

@router.get("/accept-invitation", status_code=status.HTTP_200_OK)
async def accept_invitation(
    token: str,
    current_patient: Patient = Depends(get_current_patient),
    session: AsyncSession = Depends(get_session),
):
    """
    Accept an invitation and assign the clinician to the patient.
    """
    # Validate the token
    result = await session.execute(select(InvitationToken).where(InvitationToken.token == token))
    invitation = result.scalar_one_or_none()

    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid invitation token."
        )

    if invitation.used:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This invitation token has already been used."
        )

    if invitation.expires_at < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This invitation token has expired."
        )

    # Assign the clinician to the patient
    current_patient.clinician_id = invitation.clinician_id
    session.add(current_patient)

    # Mark the token as used
    invitation.used = True
    session.add(invitation)

    await session.commit()
    await session.refresh(current_patient)

    return {"message": "You have successfully accepted the invitation."}

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