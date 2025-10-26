from fastapi import APIRouter, HTTPException
from app.schemas.user import SignupRequest, LoginRequest, UserResponse
from app.services.supabase_service import supabase
from app.schemas.config import settings
import jwt
from datetime import datetime, timedelta

router = APIRouter()

@router.post("/signup")
def signup_user(data: SignupRequest):
    """Registers a new user in Supabase."""
    try:
        result = supabase.auth.sign_up({
            "email": data.email,
            "password": data.password,
        })
        
        # Optional: Add extra user details to a users table
        supabase.table("users").insert({
            "email": data.email,
            "full_name": data.full_name or "",
            "created_at": datetime.utcnow().isoformat(),
        }).execute()

        return {"message": "Signup successful!", "user": result.user.email}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login")
def login_user(data: LoginRequest):
    """Logs a user in and returns a JWT token."""
    try:
        response = supabase.auth.sign_in_with_password({
            "email": data.email,
            "password": data.password,
        })

        if not response.user:
            raise HTTPException(status_code=401, detail="Invalid email or password")

        payload = {
            "sub": response.user.id,
            "email": data.email,
            "exp": datetime.utcnow() + timedelta(hours=2)
        }
        token = jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")

        return {"access_token": token, "token_type": "bearer"}
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))
