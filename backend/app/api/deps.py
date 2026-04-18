from __future__ import annotations

from functools import lru_cache

from app.automation_module.platforms import PlatformAutomation
from app.core.config import get_settings
from app.llm_module.ollama import OllamaProvider
from app.memory_module.store import EncryptedMemoryStore
from app.security_module.crypto import LocalEncryptor
from app.services.assistant import AssistantOrchestrator
from app.services.auth import LocalAuthService
from app.services.executor import TaskExecutor
from app.services.planner import CommandPlanner
from app.services.queue import TaskQueueManager
from app.storage.sqlite_store import SQLiteStore
from app.voice_module.stt import SpeechToText
from app.voice_module.tts import TextToSpeech


@lru_cache(maxsize=1)
def settings_store() -> SQLiteStore:
    return SQLiteStore(get_settings().database_file)


@lru_cache(maxsize=1)
def memory_store() -> EncryptedMemoryStore:
    settings = get_settings()
    return EncryptedMemoryStore(settings.memory_file, LocalEncryptor(settings.secret))


@lru_cache(maxsize=1)
def llm_provider() -> OllamaProvider:
    settings = get_settings()
    return OllamaProvider(settings.ollama_base_url, settings.ollama_model)


@lru_cache(maxsize=1)
def planner_service() -> CommandPlanner:
    settings = get_settings()
    return CommandPlanner(llm_provider(), settings.ollama_model)


@lru_cache(maxsize=1)
def task_executor() -> TaskExecutor:
    return TaskExecutor(PlatformAutomation())


@lru_cache(maxsize=1)
def queue_manager() -> TaskQueueManager:
    return TaskQueueManager(settings_store(), task_executor())


@lru_cache(maxsize=1)
def tts_engine() -> TextToSpeech:
    return TextToSpeech(get_settings().tts_engine)


@lru_cache(maxsize=1)
def assistant_service() -> AssistantOrchestrator:
    settings = get_settings()
    return AssistantOrchestrator(
        planner=planner_service(),
        queue=queue_manager(),
        memory=memory_store(),
        tts=tts_engine(),
        default_model=settings.ollama_model,
    )


@lru_cache(maxsize=1)
def stt_engine() -> SpeechToText:
    settings = get_settings()
    return SpeechToText(
        engine=settings.stt_engine,
        whisper_bin=settings.whisper_cpp_bin,
        whisper_model=settings.whisper_model_path,
        vosk_model=settings.vosk_model_path,
    )


@lru_cache(maxsize=1)
def auth_service() -> LocalAuthService:
    settings = get_settings()
    return LocalAuthService(enabled=settings.auth_enabled, password=settings.auth_password)
