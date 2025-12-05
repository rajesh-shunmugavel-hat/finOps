import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatCurrency(value: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value)
}

export function formatCurrencyPrecise(value: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value)
}

export function formatNumber(value: number): string {
  return new Intl.NumberFormat('en-US').format(value)
}

export function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

export function formatPercent(value: number): string {
  return `${value.toFixed(1)}%`
}

export function formatDuration(ms: number): string {
  if (ms < 1000) return `${ms.toFixed(0)}ms`
  if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`
  return `${(ms / 60000).toFixed(1)}m`
}

export function getStatusColor(status: string): string {
  switch (status.toUpperCase()) {
    case 'JUSTIFIED':
      return 'text-green-600 bg-green-50'
    case 'NOT_JUSTIFIED':
      return 'text-red-600 bg-red-50'
    case 'PARTIALLY_JUSTIFIED':
      return 'text-yellow-600 bg-yellow-50'
    default:
      return 'text-gray-600 bg-gray-50'
  }
}

export function getUtilizationColor(status: string): string {
  switch (status.toLowerCase()) {
    case 'severely underutilized':
      return 'text-red-600 bg-red-50'
    case 'underutilized':
      return 'text-orange-600 bg-orange-50'
    case 'optimally utilized':
      return 'text-green-600 bg-green-50'
    case 'highly utilized':
      return 'text-blue-600 bg-blue-50'
    case 'low activity':
    case 'low usage':
      return 'text-yellow-600 bg-yellow-50'
    case 'moderate activity':
      return 'text-blue-600 bg-blue-50'
    case 'high activity':
    case 'healthy':
      return 'text-green-600 bg-green-50'
    case 'high error rate':
      return 'text-red-600 bg-red-50'
    default:
      return 'text-gray-600 bg-gray-50'
  }
}

export const SERVICE_COLORS: Record<string, string> = {
  EC2: '#FF6B6B',
  RDS: '#4ECDC4',
  S3: '#45B7D1',
  Lambda: '#96CEB4',
  Other: '#DDA0DD',
}
export const SERVICE_BG = [
  "#FF6B6B",
  "#4ECDC4",
  "#45B7D1",
  "#96CEB4",
  "#DDA0DD",
]

export const CHART_COLORS = [
  '#3B82F6',
  '#10B981',
  '#F59E0B',
  '#EF4444',
  '#8B5CF6',
  '#EC4899',
  '#06B6D4',
  '#84CC16',
]
