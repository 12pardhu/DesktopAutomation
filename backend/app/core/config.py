from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    host: str = Field("127.0.0.1", alias="ASSISTANT_HOST")
    port: int = Field(8765, alias="ASSISTANT_PORT")
    secret: str = Field("dev-only-change-me", alias="ASSISTANT_SECRET")
    data_dir: Path = Field(Path("./data"), alias="ASSISTANT_DATA_DIR")

    ollama_base_url: str = Field("http://127.0.0.1:11434", alias="OLLAMA_BASE_URL")
    ollama_model: str = Field("llama3", alias="OLLAMA_MODEL")

    stt_engine: str = Field("mock", alias="STT_ENGINE")
    whisper_cpp_bin: str | None = Field(None, alias="WHISPER_CPP_BIN")
    whisper_model_path: str | None = Field(None, alias="WHISPER_MODEL_PATH")
    vosk_model_path: str | None = Field(None, alias="VOSK_MODEL_PATH")
    tts_engine: str = Field("pyttsx3", alias="TTS_ENGINE")

    auth_enabled: bool = Field(False, alias="ASSISTANT_AUTH_ENABLED")
    auth_password: str = Field("1234", alias="ASSISTANT_AUTH_PASSWORD")

    allowed_origins: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "file://",
    ]

    @property
    def memory_file(self) -> Path:
        return self.data_dir / "memory.enc"

    @property
    def audit_file(self) -> Path:
        return self.data_dir / "audit.enc"

    @property
    def database_file(self) -> Path:
        return self.data_dir / "assistant.db"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    settings = Settings()
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    return settings
