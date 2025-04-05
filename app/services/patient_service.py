from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4
from fastapi import HTTPException , status
from sqlmodel import Session, select
from app import schemas
from app.db import models
from app.schemas.patient_schema import CreateUserResponse, GetUserDetailsResponse, UpdateUserDetailsResponse
from app.utils.security import get_password_hash

class PatientService:
    def __init__(self, session: Session):
        self.session = session 

    def delete_user(self, user: models.User):
        self.session.delete(user)
        self.session.commit()


    def check_email_exists(self, email: str) -> bool:
        existing_user = self.session.exec(select(models.User).where(models.User.email == email)).first()
        return existing_user is not None

    def get_users(self, skip: int = 0, limit: int = 10) -> List[GetUserDetailsResponse]:
        if skip < 0 or limit <= 0:
            raise HTTPException(status_code=400, detail="Invalid pagination parameters")
        users = self.db.exec(select(models.User).offset(skip).limit(limit)).all()
        return [GetUserDetailsResponse.from_orm(user) for user in users]

    def get_user_by_id(self, id: UUID) -> GetUserDetailsResponse:
            user = self.session.exec(select(models.User).where(models.User.id == id)).first()
            if user  is None :
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
            return GetUserDetailsResponse.from_orm(user)
    
    def create_user(self, user: schemas.CreateUserRequest) -> CreateUserResponse:
        if self.check_email_exists(user.email):
                  raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Email already registered")
        hashed_password = get_password_hash(user.password)
        print("hashed_password is :",hashed_password)
        db_user = models.User(id=uuid4(),
                            username=user.username,
                            email=user.email,
                            hashed_password=hashed_password,
                            is_admin=False,
                            is_active=True,
                            created_at=datetime.now(),
                            updated_at=None,)  
        self.session.add(db_user)
        self.session.commit()
        self.session.refresh(db_user)
        return CreateUserResponse.from_orm(db_user)
    
    def update_user(self, user_id: UUID, user: schemas.UpdateUserRequest) -> UpdateUserDetailsResponse:
        db_user = self.session.get(models.User, user_id)
        if db_user:        
            if user.username:
               db_user.username = user.username
            if user.email:
                if self.check_email_exists(user.email):
                  raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Email already registered")
                db_user.email = user.email
            if user.password:
                hashed_password = get_password_hash(user.password)
                db_user.password = hashed_password
            db_user.updated_at = datetime.now() 
            self.session.commit()
            self.session.refresh(db_user)
            return UpdateUserDetailsResponse.from_orm(db_user)
        else :
            raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="user not found")
            


   