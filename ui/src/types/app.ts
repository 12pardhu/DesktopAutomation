export type TaskDefinition = {
  action: string;
  app?: string | null;
  path?: string | null;
  filename?: string | null;
  text?: string | null;
  selector?: string | null;
  x?: number | null;
  y?: number | null;
  seconds?: number | null;
  button?: string | null;
  url?: string | null;
  metadata?: Record<string, unknown>;
};

export type TaskPlan = {
  tasks: TaskDefinition[];
};

export type ChatMessage = {
  role: "user" | "assistant";
  content: string;
  timestamp: string;
};

export type ChatResponse = {
  reply: string;
  language: string;
  model: string;
  plan: TaskPlan;
  run_id?: string | null;
  status: string;
  created_at: string;
};

export type TaskStepRecord = {
  id: string;
  run_id: string;
  step_index: number;
  action: string;
  parameters: Record<string, unknown>;
  status: string;
  started_at?: string | null;
  finished_at?: string | null;
  message?: string | null;
  result: Record<string, unknown>;
};

export type RunRecord = {
  id: string;
  command_id: string;
  status: string;
  started_at?: string | null;
  finished_at?: string | null;
  current_step: number;
  total_steps: number;
  last_message?: string | null;
  steps: TaskStepRecord[];
};

export type CommandHistoryItem = {
  id: string;
  command: string;
  language: string;
  status: string;
  reply: string;
  model: string;
  created_at: string;
  updated_at: string;
  run_id?: string | null;
  task_count: number;
};

export type MemoryRecord = {
  id: string;
  kind: string;
  content: string;
  created_at: string;
  metadata: Record<string, unknown>;
};

export type VoiceLog = {
  timestamp: string;
  engine: string;
  transcript: string;
  detected_language: string;
  confidence?: number | null;
};

export type AnalyticsSummary = {
  total_commands: number;
  completed_runs: number;
  failed_runs: number;
  queued_runs: number;
  running_runs: number;
  success_rate: number;
  total_steps: number;
  top_actions: Array<{ action: string; count: number }>;
};

export type SettingsPayload = {
  language: string;
  mic_sensitivity: number;
  security_enabled: boolean;
  model: string;
  speak_replies: boolean;
};

export type LoginResponse = {
  enabled: boolean;
  token?: string | null;
  message: string;
};
