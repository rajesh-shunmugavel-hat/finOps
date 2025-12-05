import { ReactNode } from 'react'
import { cn } from '../lib/utils'
import { TrendingUp, TrendingDown, Minus } from 'lucide-react'

interface MetricCardProps {
  title: string
  value: string | number
  subtitle?: string
  icon?: ReactNode
  trend?: number
  trendLabel?: string
  className?: string
  valueClassName?: string
}

export default function MetricCard({
  title,
  value,
  subtitle,
  icon,
  trend,
  trendLabel,
  className,
  valueClassName,
}: MetricCardProps) {
  const getTrendIcon = () => {
    if (trend === undefined) return null
    if (trend > 0) return <TrendingUp className="h-4 w-4 text-red-500" />
    if (trend < 0) return <TrendingDown className="h-4 w-4 text-green-500" />
    return <Minus className="h-4 w-4 text-gray-400" />
  }

  const getTrendColor = () => {
    if (trend === undefined) return ''
    if (trend > 0) return 'text-red-600'
    if (trend < 0) return 'text-green-600'
    return 'text-gray-500'
  }

  return (
    <div className={cn('card', className)}>
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <p className="text-sm font-medium text-gray-500">{title}</p>
          <p className={cn('text-2xl font-bold text-gray-900 mt-1', valueClassName)}>
            {value}
          </p>
          {subtitle && (
            <p className="text-sm text-gray-500 mt-1">{subtitle}</p>
          )}
          {trend !== undefined && (
            <div className={cn('flex items-center gap-1 mt-2', getTrendColor())}>
              {getTrendIcon()}
              <span className="text-sm font-medium">
                {trend > 0 ? '+' : ''}{trend.toFixed(1)}%
              </span>
              {trendLabel && (
                <span className="text-gray-500 text-sm">{trendLabel}</span>
              )}
            </div>
          )}
        </div>
        {icon && (
          <div className="p-2 bg-blue-50 rounded-lg">
            {icon}
          </div>
        )}
      </div>
    </div>
  )
}
