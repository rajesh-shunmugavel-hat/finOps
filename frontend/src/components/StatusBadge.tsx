import { cn, getStatusColor, getUtilizationColor } from '../lib/utils'

interface StatusBadgeProps {
  status: string
  type?: 'justification' | 'utilization'
  className?: string
}

export default function StatusBadge({ status, type = 'justification', className }: StatusBadgeProps) {
  const colorClass = type === 'justification' 
    ? getStatusColor(status)
    : getUtilizationColor(status)

  const displayText = status.replace(/_/g, ' ')

  return (
    <span className={cn(
      'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium',
      colorClass,
      className
    )}>
      {displayText}
    </span>
  )
}
