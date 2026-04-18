from __future__ import annotations

import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, File, Form, Header, HTTPException, UploadFile

from app.api.deps import (
    assistant_service,
    auth_service,
    llm_provider,
    memory_store,
    settings_store,
    stt_engine,
    tts_engine,
)
from app.core.config import get_settings
from app.schemas.models import (
    ChatRequest,
    ChatResponse,
    CommandHistoryItem,
    LoginRequest,
    LoginResponse,
    MemoryRecord,
    RunRecord,
    SettingsUpdate,
    VoiceLog,
)

router = APIRouter()


def require_auth(token: str | None) -> None:
    if auth_service().validate(token):
        return
    raise HTTPException(status_code=401, detail="Authentication required")


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "mode": "offline-local", "model": get_settings().ollama_model}


@router.post("/api/auth/login", response_model=LoginResponse)
async def login(request: LoginRequest) -> LoginResponse:
    service = auth_service()
    if not service.enabled:
        return LoginResponse(enabled=False, token=None, message="Local login is disabled.")
    token = service.login(request.password)
    if token is None:
        raise HTTPException(status_code=401, detail="Invalid local password")
    return LoginResponse(enabled=True, token=token, message="Login successful")


@router.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, x_session_token: str | None = Header(default=None)) -> ChatResponse:
    require_auth(x_session_token)
    settings = get_settings()
    submission = await assistant_service().submit_command(
        message=request.message,
        requested_language=request.language.value,
        model=request.model or settings.ollama_model,
        speak_reply=request.speak_reply,
        auto_execute=request.auto_execute,
        store_create_command=settings_store().create_command,
    )
    return assistant_service().response_from_submission(submission)


@router.get("/api/models")
async def models() -> dict[str, list[str]]:
    try:
        available = await llm_provider().list_models()
    except Exception:
        available = []
    return {"models": available}


@router.get("/api/history", response_model=list[CommandHistoryItem])
async def history(x_session_token: str | None = Header(default=None)) -> list[CommandHistoryItem]:
    require_auth(x_session_token)
    return settings_store().list_commands()


@router.get("/api/runs/active", response_model=list[RunRecord])
async def active_runs(x_session_token: str | None = Header(default=None)) -> list[RunRecord]:
    require_auth(x_session_token)
    return settings_store().list_active_runs()


@router.get("/api/runs/{run_id}", response_model=RunRecord)
async def get_run(run_id: str, x_session_token: str | None = Header(default=None)) -> RunRecord:
    require_auth(x_session_token)
    run = settings_store().get_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")
    return run


@router.get("/api/analytics")
async def analytics(x_session_token: str | None = Header(default=None)):
    require_auth(x_session_token)
    return settings_store().analytics()


@router.get("/api/memory", response_model=list[MemoryRecord])
async def list_memory(x_session_token: str | None = Header(default=None)) -> list[MemoryRecord]:
    require_auth(x_session_token)
    return memory_store().list_records()


@router.delete("/api/memory")
async def clear_memory(x_session_token: str | None = Header(default=None)) -> dict[str, str]:
    require_auth(x_session_token)
    memory_store().clear()
    return {"status": "cleared"}


@router.get("/api/settings")
async def get_saved_settings(x_session_token: str | None = Header(default=None)) -> dict[str, object]:
    require_auth(x_session_token)
    saved = settings_store().load_settings()
    return {
        "language": saved.get("language", "auto"),
        "mic_sensitivity": saved.get("mic_sensitivity", 0.65),
        "security_enabled": saved.get("security_enabled", get_settings().auth_enabled),
        "model": saved.get("model", get_settings().ollama_model),
        "speak_replies": saved.get("speak_replies", False),
    }


@router.post("/api/settings")
async def update_settings(update: SettingsUpdate, x_session_token: str | None = Header(default=None)) -> dict[str, object]:
    require_auth(x_session_token)
    payload = update.model_dump(exclude_none=True)
    settings_store().save_settings(payload)
    return {"status": "saved", "settings": payload}


@router.post("/api/voice/transcribe", response_model=VoiceLog)
async def transcribe_voice(
    file: UploadFile = File(...),
    language: str = Form(default="auto"),
    x_session_token: str | None = Header(default=None),
) -> VoiceLog:
    require_auth(x_session_token)
    suffix = Path(file.filename or "voice.wav").suffix or ".wav"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        with file.file as source:
            shutil.copyfileobj(source, tmp)
        tmp.flush()
        tmp_path = Path(tmp.name)
    try:
        transcript, detected_language, confidence = stt_engine().transcribe(tmp_path, requested_language=language)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return VoiceLog(
        timestamp=datetime.now(timezone.utc),
        engine=stt_engine().engine,
        transcript=transcript,
        detected_language=detected_language,
        confidence=confidence,
    )


@router.post("/api/voice/speak")
async def speak(payload: dict[str, str], x_session_token: str | None = Header(default=None)) -> dict[str, str]:
    require_auth(x_session_token)
    text = payload.get("text", "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="text is required")
    tts_engine().speak(text)
    return {"status": "spoken"}
