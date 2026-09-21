from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
  # WhatsApp API
  whatsapp_token: str = ""
  whatsapp_phone_id: str = ""
  whatsapp_api_version: str = "v26.0"
  verify_token: str = ""

  # Gemini AI
  gemini_api_key: str = ""
  gemini_model: str = "gemini-3.6-flash"

  # Server
  app_host: str = "0.0.0.0"
  app_port: int = 8000
  debug: bool = True

  # Turso DB
  turso_database_url: str = ""
  turso_auth_token: str = ""

  model_config = SettingsConfigDict(
      env_file=".env", env_file_encoding="utf-8", extra="ignore"
  )


settings = Settings()