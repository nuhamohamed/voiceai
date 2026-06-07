import * as React from 'react';
import { SearchIcon } from 'lucide-react';
import type { MossContextEvent } from '@/hooks/useMossContextEvents';
import { cn } from '@/lib/shadcn/utils';

interface MossResultsPanelProps extends React.HTMLAttributes<HTMLDivElement> {
  events: MossContextEvent[];
  hidden?: boolean;
}

export function MossResultsPanel({
  events,
  hidden = false,
  className,
  ...props
}: MossResultsPanelProps) {
  if (hidden || events.length === 0) {
    return null;
  }

  return (
    <div className={cn('space-y-3', className)} {...props}>
      <h3 className="text-muted-foreground flex items-center gap-1.5 text-sm font-medium tracking-wide uppercase">
        <SearchIcon className="size-3.5" aria-hidden />
        Moss source
      </h3>
      <div className="space-y-2">
        {events.map(({ id, query, matches, timeTakenMs }) => (
          <details
            key={id}
            className="border-border bg-card text-card-foreground rounded-lg border p-3 shadow-sm"
            open
          >
            <summary className="cursor-pointer text-sm font-semibold">
              {query}
              {typeof timeTakenMs === 'number' && (
                <span className="text-muted-foreground ml-2 text-xs">
                  {timeTakenMs.toFixed(0)} ms
                </span>
              )}
            </summary>
            <ol className="text-muted-foreground mt-2 space-y-2 text-sm">
              {matches.length === 0 ? (
                <li className="italic">No knowledge matches found.</li>
              ) : (
                matches.map((match, index) => {
                  const meta = (match.metadata ?? {}) as { ref?: string; source?: string };
                  return (
                    <li key={`${id}-${index}`} className="space-y-1">
                      {meta.ref && (
                        <p className="text-foreground flex items-center gap-1 text-xs font-semibold">
                          <SearchIcon className="size-3 shrink-0" aria-hidden />
                          {meta.ref}
                          {meta.source ? ` (${meta.source})` : ''}
                        </p>
                      )}
                      <p className="leading-snug">{match.text}</p>
                      {typeof match.score === 'number' && (
                        <p className="text-muted-foreground text-xs">
                          Relevance: {match.score.toFixed(2)}
                        </p>
                      )}
                    </li>
                  );
                })
              )}
            </ol>
          </details>
        ))}
      </div>
    </div>
  );
}

interface LiveContextDockProps extends React.HTMLAttributes<HTMLDivElement> {
  events: MossContextEvent[];
}

/**
 * "Live context" dock frame for the meeting room. Always holds its shape so the
 * right-side column doesn't collapse before the first Moss retrieval arrives;
 * fills with `MossResultsPanel` results (data contract unchanged) once events land.
 */
export function LiveContextDock({ events, className, ...props }: LiveContextDockProps) {
  const hasResults = events.length > 0;

  return (
    <aside
      aria-label="Live context"
      className={cn(
        'border-border bg-card/40 flex h-full flex-col gap-3 rounded-xl border p-4',
        className
      )}
      {...props}
    >
      <div className="flex items-center justify-between">
        <h2 className="text-foreground text-sm font-semibold tracking-wide">Live context</h2>
        <span
          className={cn(
            'inline-flex items-center gap-1.5 font-mono text-[10px] font-bold tracking-wider uppercase',
            hasResults ? 'text-[#2563EB]' : 'text-muted-foreground'
          )}
        >
          <span
            aria-hidden
            className={cn(
              'size-1.5 rounded-full',
              hasResults ? 'bg-[#2563EB]' : 'bg-muted-foreground/40'
            )}
          />
          Moss
        </span>
      </div>

      <div className="min-h-0 flex-1 overflow-y-auto overscroll-contain">
        {hasResults ? (
          <MossResultsPanel events={events} />
        ) : (
          <p className="text-muted-foreground text-sm leading-snug">
            Retrieved work context appears here when Hippo answers a follow-up — grounded in real
            Slack, calendar, and Linear data from Moss.
          </p>
        )}
      </div>
    </aside>
  );
}
