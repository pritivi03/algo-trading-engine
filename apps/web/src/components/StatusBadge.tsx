import type { RunStatus } from "../api/types";

const config: Record<RunStatus, { dot: string; text: string; label: string; pulse: boolean }> = {
  pending:   { dot: "bg-gray-400",   text: "text-gray-400",   label: "Pending",   pulse: false },
  running:   { dot: "bg-green-400",  text: "text-green-400",  label: "Running",   pulse: true  },
  completed: { dot: "bg-emerald-400",text: "text-emerald-400",label: "Completed", pulse: false },
  failed:    { dot: "bg-red-500",    text: "text-red-400",    label: "Failed",    pulse: false },
};

export default function StatusBadge({ status }: { status: RunStatus }) {
  const c = config[status];
  return (
    <span className={`inline-flex items-center gap-1.5 text-xs font-medium ${c.text}`}>
      <span className="relative flex h-2 w-2">
        {c.pulse && (
          <span className={`animate-ping absolute inline-flex h-full w-full rounded-full ${c.dot} opacity-75`} />
        )}
        <span className={`relative inline-flex rounded-full h-2 w-2 ${c.dot}`} />
      </span>
      {c.label}
    </span>
  );
}