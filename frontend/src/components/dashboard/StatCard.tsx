// =============================================================================
// components/dashboard/StatCard.tsx — KPI metric card for Dashboard
// Shows a single metric: label, value, optional unit, and a trend badge
// (green = positive change vs previous period, red = negative).
// =============================================================================

interface StatCardProps {
  label: string
  value: number
  unit?: string | null
  // Percentage change vs previous period; null = no comparison available
  trend?: number | null
  // SVG path data string for the icon
  iconPath?: string
}

export function StatCard({ label, value, unit, trend, iconPath }: StatCardProps) {
  // Determine trend badge colour and arrow direction
  const hasTrend = trend !== null && trend !== undefined
  const trendPositive = hasTrend && trend! >= 0

  return (
    <div className="bg-surface-container-lowest rounded-xl p-5 shadow-ambient flex flex-col gap-3 animate-fade-in-up">
      {/* Header: icon + label */}
      <div className="flex items-center justify-between">
        <p className="text-label-md text-on-surface-variant leading-thai">{label}</p>
        {iconPath && (
          <div className="w-9 h-9 rounded-lg bg-secondary/10 flex items-center justify-center shrink-0">
            <svg
              className="w-5 h-5 text-secondary"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              strokeWidth={1.5}
              aria-hidden="true"
            >
              <path strokeLinecap="round" strokeLinejoin="round" d={iconPath} />
            </svg>
          </div>
        )}
      </div>

      {/* Value + unit */}
      <div className="flex items-end gap-1.5">
        <span className="text-headline-md font-display font-bold text-on-surface tabular-nums">
          {value.toLocaleString()}
        </span>
        {unit && (
          <span className="text-body-md text-on-surface-variant mb-0.5">{unit}</span>
        )}
      </div>

      {/* Trend badge */}
      {hasTrend && (
        <div
          className={[
            'self-start flex items-center gap-1 px-2 py-0.5 rounded-full text-label-sm font-medium',
            trendPositive
              ? 'bg-tertiary/10 text-tertiary'
              : 'bg-error-container text-on-error-container',
          ].join(' ')}
        >
          {/* Up/down arrow */}
          <svg className="w-3 h-3" viewBox="0 0 12 12" fill="currentColor" aria-hidden="true">
            {trendPositive ? (
              <path d="M6 2l4 5H2l4-5z" />
            ) : (
              <path d="M6 10L2 5h8l-4 5z" />
            )}
          </svg>
          <span>
            {trendPositive ? '+' : ''}{trend!.toFixed(1)}%
          </span>
        </div>
      )}
    </div>
  )
}

export default StatCard
