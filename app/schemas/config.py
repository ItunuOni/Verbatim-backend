from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    SUPABASE_URL: str
    SUPABASE_KEY: str
    SUPABASE_SERVICE_KEY: str
    SECRET_KEY: str
    GEMINI_API_KEY: str
    JWT_ALGORITHM: str = "HS256"
    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"
    

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
