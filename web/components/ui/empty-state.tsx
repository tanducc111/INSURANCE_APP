import type { LucideIcon } from "lucide-react";
import { Inbox } from "lucide-react";

type EmptyStateProps = {
  title: string;
  description?: string;
  icon?: LucideIcon;
};

export function EmptyState({
  description,
  icon: Icon = Inbox,
  title,
}: EmptyStateProps) {
  return (
    <div className="flex min-h-40 flex-col items-center justify-center rounded-lg border border-dashed border-border bg-white px-6 py-10 text-center">
      <span className="rounded-full bg-blue-50 p-3 text-primary">
        <Icon aria-hidden className="h-6 w-6" />
      </span>
      <p className="mt-4 text-sm font-bold text-ink">{title}</p>
      {description ? (
        <p className="mt-2 max-w-md text-sm leading-6 text-muted">
          {description}
        </p>
      ) : null}
    </div>
  );
}
