import type { LucideIcon } from "lucide-react";

export function StatusCard({ icon: Icon, label, value }: { icon: LucideIcon; label: string; value: string }) {
  return (
    <article className="rounded-lg border border-line bg-panel/95 p-4 shadow-lg shadow-black/10">
      <div className="mb-3 flex h-9 w-9 items-center justify-center rounded-lg bg-panelSoft">
        <Icon className="h-5 w-5 text-accent" />
      </div>
      <p className="text-sm text-slate-400">{label}</p>
      <p className="mt-1 truncate font-medium text-mist">{value}</p>
    </article>
  );
}
