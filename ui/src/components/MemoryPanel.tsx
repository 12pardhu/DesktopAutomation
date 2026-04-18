import type { MemoryRecord } from "../types/app";

export function MemoryPanel({
  memory,
  onClear,
}: {
  memory: MemoryRecord[];
  onClear: () => Promise<void>;
}) {
  return (
    <section className="rounded-[28px] border border-line/80 bg-panel/90 p-5 shadow-lg shadow-black/15">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h2 className="font-semibold text-mist">Encrypted memory</h2>
          <p className="text-sm text-slate-400">Recent command context stored locally.</p>
        </div>
        <button onClick={onClear} className="rounded-full border border-coral/50 px-4 py-2 text-sm text-slate-200 hover:border-coral">
          Clear
        </button>
      </div>
      <div className="mt-4 max-h-72 space-y-2 overflow-y-auto">
        {memory.length === 0 ? (
          <p className="rounded-2xl border border-dashed border-line/80 bg-panelSoft/60 px-4 py-5 text-sm text-slate-400">
            No stored context yet.
          </p>
        ) : (
          memory
            .slice(-6)
            .reverse()
            .map((item) => (
              <article key={item.id} className="rounded-2xl bg-panelSoft/80 p-3">
                <p className="text-xs uppercase tracking-[0.18em] text-accent">{item.kind}</p>
                <p className="mt-2 line-clamp-4 text-sm text-slate-300">{item.content}</p>
              </article>
            ))
        )}
      </div>
    </section>
  );
}
