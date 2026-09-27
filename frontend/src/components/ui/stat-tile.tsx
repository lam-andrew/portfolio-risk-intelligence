import type { ReactNode } from "react";

import { Card } from "@/components/ui/card";
import { cn } from "@/lib/utils";

interface StatTileProps {
  label: string;
  value: ReactNode;
  /** Short qualifier under the value — units, comparison, or as-of date. */
  detail?: ReactNode;
  /** A badge or chip encoding state, so status reads without parsing the number. */
  badge?: ReactNode;
  chart?: ReactNode;
  className?: string;
  featured?: boolean;
}

/** Summary-before-detail tile for the dashboard's top row. */
export function StatTile({
  label,
  value,
  detail,
  badge,
  chart,
  className,
  featured = false,
}: StatTileProps) {
  return (
    <Card
      className={cn(
        "orbit-stat flex min-w-0 flex-col gap-3 p-5 sm:p-6",
        featured && "orbit-stat-featured",
        className,
      )}
    >
      <span className="text-xs font-medium text-muted-foreground">{label}</span>
      <div className="flex items-end justify-between gap-3">
        <span className="font-mono text-[clamp(22px,1.7vw,30px)] font-medium leading-tight tracking-tight break-words tabular-nums">
          {value}
        </span>
        {badge}
      </div>
      {detail !== undefined && <span className="text-xs text-muted-foreground">{detail}</span>}
      {chart !== undefined && <div className="mt-1">{chart}</div>}
    </Card>
  );
}
