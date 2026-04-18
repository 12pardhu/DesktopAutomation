import { useEffect, useMemo, useState } from "react";
import type React from "react";
import {
  Activity,
  Bot,
  Database,
  Languages,
  LockKeyhole,
  Mic,
  Radar,
  ShieldCheck,
  Sparkles,
  TerminalSquare,
} from "lucide-react";
import { ChatPanel } from "./components/ChatPanel";
import { MemoryPanel } from "./components/MemoryPanel";
import { SettingsPanel } from "./components/SettingsPanel";
import { StatusCard } from "./components/StatusCard";
import {
  clearMemory,
  clearSession,
  getAnalytics,
  getSettings,
  listActiveRuns,
  listHistory,
  listMemory,
  listModels,
  login,
  saveSettings,
  sendChat,
  speakText,
  transcribeVoice,
} from "./lib/api";
import type {
  AnalyticsSummary,
  ChatMessage,
  CommandHistoryItem,
  MemoryRecord,
  RunRecord,
  SettingsPayload,
  VoiceLog,
} from "./types/app";

const defaultSettings: SettingsPayload = {
  language: "auto",
  mic_sensitivity: 0.65,
  security_enabled: false,
  model: "llama3",
  speak_replies: false,
};

const defaultAnalytics: AnalyticsSummary = {
  total_commands: 0,
  completed_runs: 0,
  failed_runs: 0,
  queued_runs: 0,
  running_runs: 0,
  success_rate: 0,
  total_steps: 0,
  top_actions: [],
};

export function App() {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      role: "assistant",
      content: "Offline automation assistant is ready. I can plan commands into JSON tasks, queue them, and execute them locally.",
      timestamp: new Date().toISOString(),
    },
  ]);
  const [voiceLogs, setVoiceLogs] = useState<VoiceLog[]>([]);
  const [models, setModels] = useState<string[]>([]);
  const [history, setHistory] = useState<CommandHistoryItem[]>([]);
  const [activeRuns, setActiveRuns] = useState<RunRecord[]>([]);
  const [analytics, setAnalytics] = useState<AnalyticsSummary>(defaultAnalytics);
  const [memory, setMemory] = useState<MemoryRecord[]>([]);
  const [settings, setSettings] = useState<SettingsPayload>(defaultSettings);
  const [isBusy, setBusy] = useState(false);
  const [authError, setAuthError] = useState<string>("");
  const [password, setPassword] = useState("");
  const [lastReply, setLastReply] = useState("Offline automation assistant is ready.");

  useEffect(() => {
    void bootstrap();
    const interval = window.setInterval(() => {
      void refreshOperationalData();
    }, 2500);
    return () => window.clearInterval(interval);
  }, []);

  const stats = useMemo(
    () => [
      { icon: Bot, label: "Local model", value: settings.model || models[0] || "llama3" },
      { icon: Mic, label: "Voice", value: "Offline STT" },
      { icon: Database, label: "Memory", value: `${memory.length} records` },
      { icon: ShieldCheck, label: "Success rate", value: `${analytics.success_rate}%` },
    ],
    [analytics.success_rate, memory.length, models, settings.model],
  );

  async function bootstrap() {
    try {
      const [availableModels, savedSettings] = await Promise.all([listModels(), getSettings()]);
      setModels(availableModels);
      setSettings({ ...defaultSettings, ...savedSettings });
      await refreshOperationalData();
      setAuthError("");
    } catch (error) {
      setAuthError(error instanceof Error ? error.message : "Backend authentication is required.");
    }
  }

  async function refreshOperationalData() {
    try {
      const [nextHistory, nextRuns, nextAnalytics, nextMemory] = await Promise.all([
        listHistory(),
        listActiveRuns(),
        getAnalytics(),
        listMemory(),
      ]);
      setHistory(nextHistory);
      setActiveRuns(nextRuns);
      setAnalytics(nextAnalytics);
      setMemory(nextMemory);
    } catch (error) {
      setAuthError(error instanceof Error ? error.message : "Unable to refresh dashboard data.");
    }
  }

  async function handleSend(text: string) {
    const userMessage: ChatMessage = { role: "user", content: text, timestamp: new Date().toISOString() };
    setMessages((current) => [...current, userMessage]);
    setBusy(true);
    try {
      const response = await sendChat(text, settings.language, settings.model, settings.speak_replies);
      const assistantContent = `${response.reply}\n\n${JSON.stringify(response.plan, null, 2)}`;
      setMessages((current) => [
        ...current,
        { role: "assistant", content: assistantContent, timestamp: new Date().toISOString() },
      ]);
      setLastReply(response.reply);
      await refreshOperationalData();
    } catch (error) {
      const message = error instanceof Error ? error.message : "The local assistant API is not reachable.";
      setMessages((current) => [...current, { role: "assistant", content: message, timestamp: new Date().toISOString() }]);
      setAuthError(message);
    } finally {
      setBusy(false);
    }
  }

  async function handleVoice(blob: Blob) {
    try {
      const log = await transcribeVoice(blob);
      setVoiceLogs((current) => [log, ...current].slice(0, 10));
      if (log.transcript) {
        await handleSend(log.transcript);
      }
    } catch (error) {
      setAuthError(error instanceof Error ? error.message : "Voice transcription failed.");
    }
  }

  async function handleSaveSettings() {
    await saveSettings(settings);
    await refreshOperationalData();
  }

  async function handleSpeakLast() {
    await speakText(lastReply);
  }

  async function handleLogin() {
    try {
      const response = await login(password);
      setAuthError(response.message);
      setPassword("");
      await bootstrap();
    } catch (error) {
      setAuthError(error instanceof Error ? error.message : "Login failed.");
    }
  }

  async function handleClearMemory() {
    await clearMemory();
    await refreshOperationalData();
  }

  return (
    <main className="min-h-screen bg-ink text-slate-100">
      <div className="mx-auto flex max-w-7xl flex-col gap-5 px-4 py-5 md:px-6">
        <header className="overflow-hidden rounded-[32px] border border-line/80 bg-panel/95 shadow-[0_30px_90px_rgba(0,0,0,0.28)]">
          <div className="flex flex-wrap items-start justify-between gap-6 px-6 py-6">
            <div className="max-w-3xl">
              <div className="inline-flex items-center gap-2 rounded-full border border-accent/20 bg-[#17343d] px-4 py-1 text-sm font-medium text-accent">
                <Sparkles className="h-4 w-4" />
                Intelligent Offline Desktop Automation Assistant
              </div>
              <h1 className="mt-4 max-w-2xl text-3xl font-semibold tracking-tight text-mist md:text-4xl">
                Local LLM orchestration for desktop commands, voice control, and execution tracking
              </h1>
              <p className="mt-3 max-w-2xl text-sm leading-7 text-slate-300">
                FastAPI, Ollama, Vosk, pyttsx3, SQLite, and a React dashboard working together without internet access.
              </p>
            </div>
            <div className="min-w-[280px] rounded-[28px] border border-line/80 bg-panelSoft/80 p-4">
              <div className="flex items-center gap-2 text-sm font-medium text-mist">
                <LockKeyhole className="h-4 w-4 text-honey" />
                Local access panel
              </div>
              <p className="mt-2 text-sm text-slate-400">{authError || "Use a password only if optional local login is enabled."}</p>
              <div className="mt-3 flex gap-2">
                <input
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                  type="password"
                  placeholder="Local password"
                  className="flex-1 rounded-full border border-line bg-ink/70 px-4 py-2 text-sm text-mist outline-none focus:border-accent"
                />
                <button onClick={handleLogin} className="rounded-full bg-honey px-4 py-2 text-sm font-semibold text-ink">
                  Unlock
                </button>
              </div>
              <button onClick={clearSession} className="mt-3 text-sm text-slate-400 underline decoration-line underline-offset-4">
                Clear local session
              </button>
            </div>
          </div>
        </header>

        <section className="grid gap-4 md:grid-cols-4">
          {stats.map((item) => (
            <StatusCard key={item.label} icon={item.icon} label={item.label} value={item.value} />
          ))}
        </section>

        <section className="grid gap-5 xl:grid-cols-[1.55fr_1fr]">
          <ChatPanel
            messages={messages}
            isBusy={isBusy}
            speakReplies={settings.speak_replies}
            onSend={handleSend}
            onVoice={handleVoice}
            onSpeakLast={handleSpeakLast}
          />
          <div className="grid gap-5">
            <SettingsPanel models={models} settings={settings} onChange={setSettings} onSave={handleSaveSettings} />
            <MemoryPanel memory={memory} onClear={handleClearMemory} />
          </div>
        </section>

        <section className="grid gap-5 lg:grid-cols-[1.3fr_1fr]">
          <Panel
            icon={<Radar className="h-5 w-5 text-accent" />}
            title="Real-time execution tracker"
            subtitle="Queued and running task chains"
          >
            {activeRuns.length === 0 ? (
              <EmptyState text="No active runs. Submit a command to populate the queue." />
            ) : (
              <div className="space-y-4">
                {activeRuns.map((run) => (
                  <article key={run.id} className="rounded-[24px] border border-line/80 bg-panelSoft/80 p-4">
                    <div className="flex flex-wrap items-center justify-between gap-3">
                      <div>
                        <p className="text-sm font-semibold text-mist">{run.status.toUpperCase()}</p>
                        <p className="mt-1 text-xs text-slate-400">
                          Step {run.current_step || 0} of {run.total_steps}
                        </p>
                      </div>
                      <div className="rounded-full bg-ink/60 px-3 py-1 text-xs text-slate-300">{run.id.slice(0, 8)}</div>
                    </div>
                    <div className="mt-3 h-2 overflow-hidden rounded-full bg-ink/80">
                      <div
                        className="h-full rounded-full bg-gradient-to-r from-accent to-honey"
                        style={{ width: `${run.total_steps ? (run.current_step / run.total_steps) * 100 : 0}%` }}
                      />
                    </div>
                    <div className="mt-4 space-y-2">
                      {run.steps.map((step) => (
                        <div key={step.id} className="flex items-start justify-between gap-3 rounded-2xl bg-ink/55 px-3 py-2 text-sm">
                          <div>
                            <p className="font-medium text-slate-200">
                              {step.step_index}. {step.action}
                            </p>
                            <p className="mt-1 text-xs text-slate-400">{step.message ?? JSON.stringify(step.parameters)}</p>
                          </div>
                          <span className="rounded-full border border-line px-2 py-1 text-xs text-slate-300">{step.status}</span>
                        </div>
                      ))}
                    </div>
                  </article>
                ))}
              </div>
            )}
          </Panel>

          <Panel
            icon={<Activity className="h-5 w-5 text-accent" />}
            title="Analytics"
            subtitle="Local execution summary"
          >
            <div className="grid grid-cols-2 gap-3">
              <Metric label="Commands" value={String(analytics.total_commands)} />
              <Metric label="Completed" value={String(analytics.completed_runs)} />
              <Metric label="Failed" value={String(analytics.failed_runs)} />
              <Metric label="Steps" value={String(analytics.total_steps)} />
            </div>
            <div className="mt-4 rounded-[24px] border border-line/80 bg-panelSoft/80 p-4">
              <div className="flex items-center gap-2 text-sm font-medium text-mist">
                <Languages className="h-4 w-4 text-honey" />
                Supported languages
              </div>
              <p className="mt-2 text-sm text-slate-300">English, Hindi, Telugu</p>
            </div>
            <div className="mt-4 rounded-[24px] border border-line/80 bg-panelSoft/80 p-4">
              <div className="flex items-center gap-2 text-sm font-medium text-mist">
                <TerminalSquare className="h-4 w-4 text-honey" />
                Most used actions
              </div>
              <div className="mt-3 space-y-2">
                {analytics.top_actions.length === 0 ? (
                  <p className="text-sm text-slate-400">No action data yet.</p>
                ) : (
                  analytics.top_actions.map((item) => (
                    <div key={item.action} className="flex items-center justify-between rounded-2xl bg-ink/55 px-3 py-2 text-sm">
                      <span className="text-slate-200">{item.action}</span>
                      <span className="text-slate-400">{item.count}</span>
                    </div>
                  ))
                )}
              </div>
            </div>
          </Panel>
        </section>

        <section className="grid gap-5 lg:grid-cols-2">
          <Panel icon={<Mic className="h-5 w-5 text-accent" />} title="Voice logs" subtitle="Latest offline transcriptions">
            {voiceLogs.length === 0 ? (
              <EmptyState text="No voice commands captured yet." />
            ) : (
              <div className="space-y-2">
                {voiceLogs.map((log, index) => (
                  <div key={`${log.timestamp}-${index}`} className="rounded-2xl bg-panelSoft/80 px-4 py-3 text-sm">
                    <div className="flex items-center justify-between gap-3">
                      <span className="font-medium text-mist">{log.detected_language.toUpperCase()}</span>
                      <span className="text-xs text-slate-400">{log.engine}</span>
                    </div>
                    <p className="mt-2 text-slate-300">{log.transcript}</p>
                  </div>
                ))}
              </div>
            )}
          </Panel>

          <Panel icon={<Database className="h-5 w-5 text-accent" />} title="Command history" subtitle="Persistent SQLite audit trail">
            {history.length === 0 ? (
              <EmptyState text="No command history yet." />
            ) : (
              <div className="space-y-2">
                {history.map((item) => (
                  <div key={item.id} className="rounded-2xl border border-line/80 bg-panelSoft/80 px-4 py-3 text-sm">
                    <div className="flex flex-wrap items-center justify-between gap-3">
                      <p className="font-medium text-mist">{item.command}</p>
                      <span className="rounded-full bg-ink/60 px-3 py-1 text-xs text-slate-300">{item.status}</span>
                    </div>
                    <p className="mt-2 text-slate-400">{item.reply}</p>
                    <p className="mt-2 text-xs uppercase tracking-[0.18em] text-slate-500">
                      {item.language} • {item.task_count} tasks • {item.model}
                    </p>
                  </div>
                ))}
              </div>
            )}
          </Panel>
        </section>
      </div>
    </main>
  );
}

function Panel({
  title,
  subtitle,
  icon,
  children,
}: {
  title: string;
  subtitle: string;
  icon: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <article className="rounded-[28px] border border-line/80 bg-panel/90 p-5 shadow-lg shadow-black/15">
      <div className="mb-4 flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-panelSoft">{icon}</div>
        <div>
          <h2 className="font-semibold text-mist">{title}</h2>
          <p className="text-sm text-slate-400">{subtitle}</p>
        </div>
      </div>
      {children}
    </article>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-[24px] border border-line/80 bg-panelSoft/80 p-4">
      <p className="text-sm text-slate-400">{label}</p>
      <p className="mt-1 text-2xl font-semibold text-mist">{value}</p>
    </div>
  );
}

function EmptyState({ text }: { text: string }) {
  return <p className="rounded-[24px] border border-dashed border-line/80 bg-panelSoft/60 px-4 py-5 text-sm text-slate-400">{text}</p>;
}
