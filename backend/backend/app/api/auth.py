from fastapi import APIRouter, Depends, HTTPException
from app.core.database import get_db
from app.core.dependencies import current_user
from app.core.security import hash_password, verify_password, create_access_token
from app.models.models import User
from app.schemas.common import UserCreate, LoginRequest

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register")
def register(data: UserCreate, db=Depends(get_db)):
    if db.query(User).filter(User.email == data.email.lower()).first():
        raise HTTPException(409, "Email already registered")
    allowed = {"farmer", "resource_owner", "labour_provider", "buyer", "admin"}
    if data.role not in allowed:
        raise HTTPException(400, "Invalid role")
    user = User(name=data.name, email=data.email.lower(), phone=data.phone, password_hash=hash_password(data.password), role=data.role)
    db.add(user); db.commit(); db.refresh(user)
    return {"id": user.id, "name": user.name, "email": user.email, "role": user.role}

@router.post("/login")
def login(data: LoginRequest, db=Depends(get_db)):
    user = db.query(User).filter(User.email == data.email.lower()).first()
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(401, "Invalid credentials")
    return {"access_token": create_access_token(user.id, user.role), "token_type": "bearer"}

@router.get("/me")
def me(user=Depends(current_user)):
    return {"id": user.id, "name": user.name, "email": user.email, "role": user.role}
