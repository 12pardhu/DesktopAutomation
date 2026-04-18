import type {
  AnalyticsSummary,
  ChatResponse,
  CommandHistoryItem,
  LoginResponse,
  MemoryRecord,
  RunRecord,
  SettingsPayload,
  VoiceLog,
} from "../types/app";

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://127.0.0.1:8765";
const TOKEN_KEY = "offline-assistant-token";

function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

function setToken(token: string | null) {
  if (token) {
    localStorage.setItem(TOKEN_KEY, token);
    return;
  }
  localStorage.removeItem(TOKEN_KEY);
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers ?? {});
  const token = getToken();
  if (token) {
    headers.set("x-session-token", token);
  }
  let response: Response;
  try {
    response = await fetch(`${API_BASE}${path}`, { ...init, headers });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Network request failed";
    throw new Error(
      `${message}. The local backend may not be running at ${API_BASE}. Start the FastAPI server and try again.`,
    );
  }
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `Request failed with status ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export async function login(password: string): Promise<LoginResponse> {
  const response = await request<LoginResponse>("/api/auth/login", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ password }),
  });
  setToken(response.token ?? null);
  return response;
}

export async function sendChat(message: string, language = "auto", model?: string, speakReply = false) {
  return request<ChatResponse>("/api/chat", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ message, language, model, speak_reply: speakReply, auto_execute: true }),
  });
}

export async function transcribeVoice(blob: Blob, language = "auto") {
  const formData = new FormData();
  formData.append("file", blob, "voice-command.wav");
  formData.append("language", language);
  return request<VoiceLog>("/api/voice/transcribe", {
    method: "POST",
    body: formData,
  });
}

export async function transcribeVoiceLocally(blob: Blob, language = "auto") {
  if (!window.assistantDesktop?.transcribeLocalAudio) {
    return null;
  }
  const buffer = await blob.arrayBuffer();
  return window.assistantDesktop.transcribeLocalAudio(buffer, language);
}

export async function listModels(): Promise<string[]> {
  try {
    const data = await request<{ models: string[] }>("/api/models");
    return data.models ?? [];
  } catch {
    return [];
  }
}

export async function listMemory(): Promise<MemoryRecord[]> {
  return request<MemoryRecord[]>("/api/memory");
}

export async function clearMemory() {
  return request<{ status: string }>("/api/memory", { method: "DELETE" });
}

export async function listHistory(): Promise<CommandHistoryItem[]> {
  return request<CommandHistoryItem[]>("/api/history");
}

export async function listActiveRuns(): Promise<RunRecord[]> {
  return request<RunRecord[]>("/api/runs/active");
}

export async function getRun(runId: string): Promise<RunRecord> {
  return request<RunRecord>(`/api/runs/${runId}`);
}

export async function getAnalytics(): Promise<AnalyticsSummary> {
  return request<AnalyticsSummary>("/api/analytics");
}

export async function getSettings(): Promise<SettingsPayload> {
  return request<SettingsPayload>("/api/settings");
}

export async function saveSettings(settings: Partial<SettingsPayload>) {
  return request<{ status: string; settings: Partial<SettingsPayload> }>("/api/settings", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(settings),
  });
}

export async function speakText(text: string) {
  return request<{ status: string }>("/api/voice/speak", {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ text }),
  });
}

export function clearSession() {
  setToken(null);
}
