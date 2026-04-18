import type { SettingsPayload } from "../types/app";

export function SettingsPanel({
  models,
  settings,
  onChange,
  onSave,
}: {
  models: string[];
  settings: SettingsPayload;
  onChange: (next: SettingsPayload) => void;
  onSave: () => Promise<void>;
}) {
  return (
    <section className="rounded-[28px] border border-line/80 bg-panel/90 p-5 shadow-lg shadow-black/15">
      <div className="flex items-center justify-between gap-3">
        <h2 className="font-semibold text-mist">Assistant settings</h2>
        <button onClick={onSave} className="rounded-full bg-honey px-4 py-2 text-sm font-semibold text-ink">
          Save
        </button>
      </div>
      <div className="mt-5 space-y-4">
        <label className="block text-sm text-slate-300">
          Language
          <select
            value={settings.language}
            onChange={(event) => onChange({ ...settings, language: event.target.value })}
            className="mt-2 w-full rounded-2xl border border-line bg-ink/70 px-3 py-2 text-mist outline-none focus:border-accent"
          >
            <option value="auto">Auto-detect</option>
            <option value="en">English</option>
            <option value="hi">Hindi</option>
            <option value="te">Telugu</option>
          </select>
        </label>
        <label className="block text-sm text-slate-300">
          Ollama model
          <select
            value={settings.model}
            onChange={(event) => onChange({ ...settings, model: event.target.value })}
            className="mt-2 w-full rounded-2xl border border-line bg-ink/70 px-3 py-2 text-mist outline-none focus:border-accent"
          >
            {(models.length ? models : ["llama3"]).map((model) => (
              <option key={model} value={model}>
                {model}
              </option>
            ))}
          </select>
        </label>
        <label className="block text-sm text-slate-300">
          Mic sensitivity
          <input
            type="range"
            min="0"
            max="1"
            step="0.05"
            value={settings.mic_sensitivity}
            onChange={(event) => onChange({ ...settings, mic_sensitivity: Number(event.target.value) })}
            className="mt-2 w-full accent-[#ffd36d]"
          />
        </label>
        <label className="flex items-center justify-between gap-4 rounded-2xl border border-line/80 bg-panelSoft px-4 py-3 text-sm text-slate-300">
          Speak assistant replies
          <input
            type="checkbox"
            checked={settings.speak_replies}
            onChange={(event) => onChange({ ...settings, speak_replies: event.target.checked })}
            className="h-4 w-4 accent-[#ffd36d]"
          />
        </label>
        <label className="flex items-center justify-between gap-4 rounded-2xl border border-line/80 bg-panelSoft px-4 py-3 text-sm text-slate-300">
          Local login (env controlled)
          <input
            type="checkbox"
            checked={settings.security_enabled}
            disabled
            className="h-4 w-4 accent-[#ffd36d]"
          />
        </label>
      </div>
    </section>
  );
}
