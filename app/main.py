import io
import base64
import asyncio
import time
import jwt
from datetime import datetime, timedelta

from fastapi import FastAPI, APIRouter, File, UploadFile, Form, HTTPException, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Tuple, Optional

# --- Internal Imports ---
from app.schemas.config import settings


from app.schemas.user import SignupRequest, LoginRequest
from app.services.supabase_service import supabase
from app.core.auth import verify_jwt

# --- External Libraries ---
import speech_recognition as sr
import pydub


# --- FastAPI App Setup ---
app = FastAPI(
    title="Verbatim",
    description="Speech-to-Text, Subtitle, Translation & Voice-Over Tool",
    version="1.0.0"
)

# --- CORS Configuration ---
origins = [origin.strip() for origin in settings.CORS_ORIGINS.split(",")]
if "*" not in origins:
    origins.append("*")

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- MODELS ---
class TranslationRequest(BaseModel):
    text: str
    target_code: str


class TTSRequest(BaseModel):
    text: str
    voice_name: str
    emotion_prompt: str = ""
    is_preview: bool = False


# --- HELPER FUNCTIONS ---

async def make_gemini_request(prompt: str, is_grounded: bool = False) -> str:
    """Mocks async Gemini API call."""
    await asyncio.sleep(0.5)
    if is_grounded:
        return f"Translated content based on prompt: '{prompt}'"
    return f"Generated text based on prompt: '{prompt}'"


def process_media_for_subtitles(file_stream: io.BytesIO, language_code: str) -> Tuple[str, str, Optional[str]]:
    """Mock transcription logic."""
    try:
        audio_segment = pydub.AudioSegment.from_file(file_stream, format="mp3")
        duration_ms = len(audio_segment)
        full_text = f"This is a mock transcription of the audio file in language {language_code}. It lasted {duration_ms / 1000:.2f} seconds."
        srt_content = "1\n00:00:00,000 --> 00:00:05,000\nMock Subtitle Line 1\n\n2\n00:00:05,000 --> 00:00:10,000\nMock Subtitle Line 2"
        return full_text, srt_content, None
    except Exception as e:
        return "", "", f"Audio processing error: {e}"


async def translate_text(text: str, target_code: str) -> Tuple[str, Optional[str]]:
    """Mock text translation logic."""
    try:
        prompt = f"Translate the following text to language '{target_code}':\n\n{text}"
        translated_text = await make_gemini_request(prompt)
        return translated_text, None
    except Exception as e:
        return "", f"Translation failed: {e}"


async def generate_tts_audio(text: str, voice_name: str, emotion_prompt: str = "") -> Tuple[str, Optional[str]]:
    """Mock TTS generation logic."""
    try:
        await asyncio.sleep(1)
        mock_audio_data = b"MOCK_PCM_AUDIO_DATA_FOR_TTS"
        encoded_audio = base64.b64encode(mock_audio_data).decode('utf-8')
        return encoded_audio, None
    except Exception as e:
        return "", f"TTS generation failed: {e}"


# --- AUTHENTICATION ROUTES ---

@app.post("/auth/signup")
def signup_user(data: SignupRequest):
    """Registers a new user in Supabase."""
    try:
        result = supabase.auth.sign_up({
            "email": data.email,
            "password": data.password,
        })

        # Optional: Add user to custom users table
        supabase.table("users").insert({
            "email": data.email,
            "full_name": data.full_name or "",
            "created_at": datetime.utcnow().isoformat(),
        }).execute()

        return {"message": "Signup successful!", "user": data.email}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Signup failed: {e}")


@app.post("/auth/login")
def login_user(data: LoginRequest):
    """Logs a user in and returns JWT token."""
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

        return {"message": "Login successful!", "access_token": token, "token_type": "bearer"}
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Login failed: {e}")


# --- HEALTH CHECKS ---

@app.get("/")
async def root():
    return {"message": "Verbatim API is running", "version": "1.0.0", "status": "healthy"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


# --- PROTECTED ROUTES ---

@app.post("/transcribe")
async def transcribe_media(
    file: UploadFile = File(...),
    language_code: str = Form(...),
    user: dict = Depends(verify_jwt)
):
    """Handles file upload for transcription and subtitle generation."""
    if not file.content_type or not file.content_type.startswith('audio/'):
        raise HTTPException(status_code=400, detail="Only audio files are supported.")

    file_stream = io.BytesIO(await file.read())
    final_text, srt_content, error_message = process_media_for_subtitles(file_stream, language_code)

    if error_message:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {error_message}")

    # Log activity
    supabase.table("user_activities").insert({
        "email": user.get("email"),
        "action": "transcription",
        "timestamp": datetime.utcnow().isoformat()
    }).execute()

    return {"full_text": final_text, "srt_content": srt_content}


@app.post("/translate")
async def handle_translation(
    data: TranslationRequest,
    user: dict = Depends(verify_jwt)
):
    """Translates text using Gemini mock API."""
    translated_text, error_message = await translate_text(data.text, data.target_code)

    if error_message:
        raise HTTPException(status_code=500, detail=f"Translation error: {error_message}")

    # Log activity
    supabase.table("user_activities").insert({
        "email": user.get("email"),
        "action": "translation",
        "timestamp": datetime.utcnow().isoformat()
    }).execute()

    return {"translated_text": translated_text}


@app.post("/voiceover")
async def handle_tts(
    data: TTSRequest,
    user: dict = Depends(verify_jwt)
):
    """Generates mock TTS voice-over."""
    audio_base64, error_message = await generate_tts_audio(data.text, data.voice_name, data.emotion_prompt)

    if error_message:
        raise HTTPException(status_code=500, detail=f"Voice-over generation error: {error_message}")

    # Log activity
    supabase.table("user_activities").insert({
        "email": user.get("email"),
        "action": "voiceover",
        "timestamp": datetime.utcnow().isoformat()
    }).execute()

    return JSONResponse(content={"audio_base64": audio_base64})


# --- MAIN RUNNER ---

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True
    )
