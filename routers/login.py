from fastapi import Depends, HTTPException, APIRouter
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from database import models
from database.get_db import get_db
from schemas.user_schema import LoginInput, RegisterInput

from auth.auth import get_current_user

from sqlalchemy.orm import Session

from utils.functions import verify_password, generate_access_token, generate_hash
from uuid import uuid4

router = APIRouter(prefix="/api/v1", tags=["Authentication"])


@router.get("/ping")
def ping(user_id: int = Depends(get_current_user)):
    return {"status": "alive"}

@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    if user and verify_password(form_data.password, user.password):
        data: dict = {
            "user_id": user.id,
            "names": user.names,
            "email": user.email,
            "phone": user.phone,
            "role": user.role
        }
        access_token = generate_access_token(data={"sub": str(user.id)})
        return {
            "message": "User logged in successfully",
            "user_data": data,
            "access_token": access_token,
            "token_type": "bearer"
        }
    raise HTTPException(status_code=401, detail="Invalid email or password")

@router.post("/register")
def register_user(u: RegisterInput, db: Session = Depends(get_db)):
    existing_user = db.query(models.User).filter(models.User.email == u.email).first()
    if existing_user and (u.phone == existing_user.phone):
        raise HTTPException(status_code=401, detail="User Already Exists. Try Another Email")
    
    new_user = models.User(
        id=uuid4(),
        names=str(u.names),
        email=str(u.email),
        phone=int(u.phone),
        password=generate_hash(str(u.password)),
        role=",".join([r.value for r in u.role])
    )
    user_data: dict = {
        "user_id": new_user.id,
        "names": u.names,
        "email": u.email,
        "phone": u.phone,
        "role": u.role
    }
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "User Registered Well", "user_data": user_data}

