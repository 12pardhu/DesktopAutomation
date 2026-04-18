from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


class Language(str, Enum):
    auto = "auto"
    english = "en"
    hindi = "hi"
    telugu = "te"


class TaskAction(str, Enum):
    open_app = "open_app"
    navigate_directory = "navigate_directory"
    search_file = "search_file"
    open_file = "open_file"
    type_text = "type_text"
    click = "click"
    wait = "wait"
    open_url = "open_url"


class TaskDefinition(BaseModel):
    action: TaskAction
    app: str | None = None
    path: str | None = None
    filename: str | None = None
    text: str | None = None
    selector: str | None = None
    x: int | None = None
    y: int | None = None
    seconds: float | None = Field(default=None, ge=0)
    button: Literal["left", "right", "middle"] | None = "left"
    url: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class TaskPlan(BaseModel):
    tasks: list[TaskDefinition] = Field(default_factory=list)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=8000)
    language: Language = Language.auto
    model: str | None = None
    speak_reply: bool = False
    auto_execute: bool = True


class CommandSubmission(BaseModel):
    id: str
    command: str
    language: str
    model: str
    reply: str
    plan: TaskPlan
    run_id: str | None = None
    status: str
    created_at: datetime


class ChatResponse(BaseModel):
    reply: str
    language: str
    model: str
    plan: TaskPlan
    run_id: str | None = None
    status: str
    created_at: datetime


class VoiceLog(BaseModel):
    timestamp: datetime
    engine: str
    transcript: str
    detected_language: str
    confidence: float | None = None


class TaskStepRecord(BaseModel):
    id: str
    run_id: str
    step_index: int
    action: str
    parameters: dict[str, Any] = Field(default_factory=dict)
    status: str
    started_at: datetime | None = None
    finished_at: datetime | None = None
    message: str | None = None
    result: dict[str, Any] = Field(default_factory=dict)


class CommandHistoryItem(BaseModel):
    id: str
    command: str
    language: str
    status: str
    reply: str
    model: str
    created_at: datetime
    updated_at: datetime
    run_id: str | None = None
    task_count: int = 0


class RunRecord(BaseModel):
    id: str
    command_id: str
    status: str
    started_at: datetime | None = None
    finished_at: datetime | None = None
    current_step: int = 0
    total_steps: int = 0
    last_message: str | None = None
    steps: list[TaskStepRecord] = Field(default_factory=list)


class AnalyticsSummary(BaseModel):
    total_commands: int = 0
    completed_runs: int = 0
    failed_runs: int = 0
    queued_runs: int = 0
    running_runs: int = 0
    success_rate: float = 0.0
    total_steps: int = 0
    top_actions: list[dict[str, Any]] = Field(default_factory=list)


class SystemAction(BaseModel):
    id: str
    timestamp: datetime
    action: str
    target: str
    status: str
    requires_confirmation: bool = False
    detail: str | None = None


class SettingsUpdate(BaseModel):
    language: Language | None = None
    mic_sensitivity: float | None = Field(None, ge=0.0, le=1.0)
    security_enabled: bool | None = None
    model: str | None = None
    speak_replies: bool | None = None


class MemoryRecord(BaseModel):
    id: str
    kind: str
    content: str
    created_at: datetime
    metadata: dict[str, Any] = Field(default_factory=dict)


class LoginRequest(BaseModel):
    password: str = Field(min_length=1, max_length=128)


class LoginResponse(BaseModel):
    enabled: bool
    token: str | None = None
    message: str
