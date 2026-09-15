from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    whatsapp_token: str
    whatsapp_phone_id: str
    whatsapp_api_version: str = "v21.0"
    verify_token: str
    gemini_api_key: str
    gemini_model: str = "gemini-3.6-flash"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    debug: bool = True

    class Config:
        env_file = ".env"

settings = Settings()