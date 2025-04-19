import asyncio
from typing import Tuple
from fastapi import APIRouter, Depends, HTTPException, Query, status ,BackgroundTasks
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from app.db.database import get_session
from app.schemas.game_result_schema import GameResultCropCreate, GameResultMatchingCreate, GameResultSequenceCreate
from app.schemas.sessions_schema import SessionCreate, SessionCreateResponse, SessionResponse
from app.services.attention_analysis_service import AttentionAnalysisService
from app.services.game_result_services import GameResultService
from app.api.dependinces import get_current_patient, get_current_user
from app.db.models import Patient, User, UserRole
from app.services.memory_analysis_services import MemoryAnalysisService
from app.services.mini_games_services import MiniGameService
from app.services.session_service import SessionService

router = APIRouter(tags=["Game Results"])

# @router.post(
#     "/game-results",
#     response_model=GameResultResponse,
#     status_code=status.HTTP_201_CREATED,
#     summary="Create a new game result",
#     description="Endpoint to create a new game result for a specific session."
# )
# async def create_game_result(
#     game_result_data: GameResultCreate,
#     session: AsyncSession = Depends(get_session),
#     current_user: Tuple[User, UserRole] = Depends(get_current_user)  # Unpack the tuple
# ):
#     user, role = current_user  # Unpack the tuple into user and role

#     service = GameResultService(session)
#     return await service.create_game_result(game_result_data, user.user_id)

# @router.get(
#     "/game-results/{user_id}",
#     response_model=list[GameResultResponse],
#     status_code=status.HTTP_200_OK,
#     summary="Retrieve game results for a specific user",
#     description="Endpoint to retrieve all game results for a specific user. Accessible by the user or their doctor."
# )
# async def get_game_results_for_user(
#     user_id: UUID,
#     session: AsyncSession = Depends(get_session),
#     current_user: Tuple[User, UserRole] = Depends(get_current_user)  # Unpack the tuple
# ):
#     user, role = current_user  # Unpack the tuple into user and role

#     # If the current user is a patient, ensure they are retrieving their own data
#     if role == UserRole.PATIENT and user.user_id != user_id:
#         raise HTTPException(
#             status_code=status.HTTP_403_FORBIDDEN,
#             detail="You do not have permission to access these game results"
#         )

#     # If the current user is a doctor, ensure they are associated with the patient
#     if role == UserRole.DOCTOR:
#         result = await session.execute(
#             select(Patient).where(Patient.user_id == user_id, Patient.clinician_id == user.user_id)
#         )
#         patient = result.scalar_one_or_none()
#         if not patient:
#             raise HTTPException(
#                 status_code=status.HTTP_403_FORBIDDEN,
#                 detail="You do not have permission to access these game results"
#             )

#     # Retrieve game results for the specified user
#     service = GameResultService(session)
#     return await service.get_game_results_by_user_id(user_id)

@router.get(
    "/user-data/{user_id}",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Retrieve all sessions, game results, and mini-game matrices for a user",
    description="Endpoint to retrieve all sessions, game results, and mini-game matrices for a specific user. Accessible by the user or their doctor."
)
async def get_user_data(
    user_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: Tuple[User, UserRole] = Depends(get_current_user),
    limit: int = Query(10, ge=1, le=100),  # Limit the number of results (default: 10, max: 100)
    offset: int = Query(0, ge=0) 
):
    user, role = current_user

    # Authorization checks
    if role == UserRole.PATIENT and user.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this data"
        )

    if role == UserRole.DOCTOR:
        result = await session.execute(
            select(Patient).where(Patient.user_id == user_id, Patient.clinician_id == user.user_id)
        )
        patient = result.scalar_one_or_none()
        if not patient:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to access this data"
            )

    # Retrieve data
    session_service = SessionService(session)
    game_result_service = GameResultService(session)

    sessions = await session_service.get_sessions_by_patient_id(user_id , limit , offset)
    game_results = await game_result_service.get_game_results_by_user_id(user_id)

    return {
        "sessions": sessions,
        "game_results": game_results,
    }

@router.post(
        "/user-data/",
        response_model=SessionResponse,
        status_code=status.HTTP_201_CREATED,
        summary="Create sessions, game results, and mini-game matrices for a user",
        description="Endpoint to create new sessions, game results, and mini-game matrices for a specific user. Only accessible by the user."
    )
async def create_user_data(
        session_data: SessionCreate,  
        background_tasks: BackgroundTasks,
        user_id: UUID = Query(..., description="The ID of the user"),  # Add user_id as a query parameter
        session: AsyncSession = Depends(get_session),
        background_session: AsyncSession = Depends(get_session),
        current_user: Patient = Depends(get_current_patient),
    ):
        # Authorization check: Only the current patient can create data
        if current_user.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to create data for this user."
            )
        session_data.user_id = user_id
        # Use the SessionService to create the session and associated data
        service = SessionService(session )
        created_session_response = await service.create_session(session_data , user_id)

        memory_analysis_service = MemoryAnalysisService(background_session)
        attention_analysis_service = AttentionAnalysisService(background_session)
 
    #     background_tasks.add_task(
    #         attention_analysis_service.calculate_and_save_attention_analysis,
    #         created_session_response.session_id,
    #    )
        background_tasks.add_task(
            memory_analysis_service.calculate_and_save_memory_analysis,
            created_session_response.session_id,
            current_user.date_of_birth
        )

        return created_session_response



