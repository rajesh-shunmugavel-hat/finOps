import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { format } from 'date-fns'
import { 
  ArrowLeft, FileText, TrendingDown, Clock, DollarSign,
  Server, Database, HardDrive, Zap, ChevronDown, ChevronUp
} from 'lucide-react'
import { getReport, type AIReport } from '../lib/api'
import { formatCurrency, formatPercent, SERVICE_COLORS } from '../lib/utils'
import LoadingSpinner from '../components/LoadingSpinner'
import StatusBadge from '../components/StatusBadge'

const SERVICE_ICONS: Record<string, any> = {
  EC2: Server,
  RDS: Database,
  S3: HardDrive,
  Lambda: Zap,
}

export default function ReportDetail() {
  const { reportId } = useParams<{ reportId: string }>()
  const [report, setReport] = useState<AIReport | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [expandedFindings, setExpandedFindings] = useState<Set<number>>(new Set())

  useEffect(() => {
    if (reportId) {
      loadReport()
    }
  }, [reportId])

  const loadReport = async () => {
    try {
      setLoading(true)
      const data = await getReport(parseInt(reportId!))
      setReport(data)
      if (data.recommendations.length > 0) {
        setExpandedFindings(new Set([data.recommendations[0].id]))
      }
    } catch (err) {
      setError('Failed to load report')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const toggleFinding = (id: number) => {
    setExpandedFindings(prev => {
      const next = new Set(prev)
      if (next.has(id)) {
        next.delete(id)
      } else {
        next.add(id)
      }
      return next
    })
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  if (error || !report) {
    return (
      <div className="text-center py-12">
        <p className="text-red-600">{error || 'Failed to load report'}</p>
        <Link to="/reports" className="btn-primary mt-4 inline-block">
          Back to Reports
        </Link>
      </div>
    )
  }

  const savingsPercentage = report.total_current_spend > 0 
    ? (report.total_monthly_savings / report.total_current_spend * 100)
    : 0

  const findingsByStatus = {
    NOT_JUSTIFIED: report.recommendations.filter(r => r.justification_status === 'NOT_JUSTIFIED'),
    PARTIALLY_JUSTIFIED: report.recommendations.filter(r => r.justification_status === 'PARTIALLY_JUSTIFIED'),
    JUSTIFIED: report.recommendations.filter(r => r.justification_status === 'JUSTIFIED'),
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Link
          to="/reports"
          className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
        >
          <ArrowLeft className="h-5 w-5 text-gray-600" />
        </Link>
        <div className="flex items-center gap-3">
          <div className="p-3 bg-blue-50 rounded-xl">
            <FileText className="h-6 w-6 text-blue-600" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Analysis Report #{report.id}</h1>
            <p className="text-gray-500 flex items-center gap-1">
              <Clock className="h-4 w-4" />
              {format(new Date(report.analysis_date), 'MMMM d, yyyy h:mm a')}
            </p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="card">
          <p className="text-sm text-gray-500">Current Monthly Spend</p>
          <p className="text-2xl font-bold text-gray-900 mt-1">{formatCurrency(report.total_current_spend)}</p>
        </div>
        <div className="card">
          <p className="text-sm text-gray-500">Potential Savings</p>
          <p className="text-2xl font-bold text-green-600 mt-1 flex items-center gap-1">
            <TrendingDown className="h-5 w-5" />
            {formatCurrency(report.total_monthly_savings)}
          </p>
        </div>
        <div className="card">
          <p className="text-sm text-gray-500">Savings Percentage</p>
          <p className="text-2xl font-bold text-green-600 mt-1">{formatPercent(savingsPercentage)}</p>
        </div>
        <div className="card">
          <p className="text-sm text-gray-500">Optimization Findings</p>
          <p className="text-2xl font-bold text-gray-900 mt-1">{report.optimization_count}</p>
        </div>
      </div>

      {report.executive_summary && (
        <div className="card bg-gradient-to-r from-blue-50 to-indigo-50 border-blue-200">
          <h2 className="text-lg font-semibold text-gray-900 mb-2">Executive Summary</h2>
          <p className="text-gray-700 leading-relaxed">{report.executive_summary}</p>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="card bg-red-50 border-red-100">
          <div className="flex items-center justify-between">
            <h3 className="font-medium text-red-800">Not Justified</h3>
            <span className="text-2xl font-bold text-red-600">{findingsByStatus.NOT_JUSTIFIED.length}</span>
          </div>
          <p className="text-sm text-red-600 mt-1">Immediate optimization needed</p>
        </div>
        <div className="card bg-yellow-50 border-yellow-100">
          <div className="flex items-center justify-between">
            <h3 className="font-medium text-yellow-800">Partially Justified</h3>
            <span className="text-2xl font-bold text-yellow-600">{findingsByStatus.PARTIALLY_JUSTIFIED.length}</span>
          </div>
          <p className="text-sm text-yellow-600 mt-1">Review recommended</p>
        </div>
        <div className="card bg-green-50 border-green-100">
          <div className="flex items-center justify-between">
            <h3 className="font-medium text-green-800">Justified</h3>
            <span className="text-2xl font-bold text-green-600">{findingsByStatus.JUSTIFIED.length}</span>
          </div>
          <p className="text-sm text-green-600 mt-1">Well optimized</p>
        </div>
      </div>

      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Detailed Findings</h2>
        <div className="space-y-4">
          {report.recommendations.map((rec, index) => {
            const Icon = SERVICE_ICONS[rec.service_name] || Server
            const serviceColor = SERVICE_COLORS[rec.service_name] || '#3B82F6'
            const isExpanded = expandedFindings.has(rec.id)

            return (
              <div
                key={rec.id}
                className="border border-gray-200 rounded-lg overflow-hidden"
              >
                <button
                  onClick={() => toggleFinding(rec.id)}
                  className="w-full p-4 flex items-center justify-between bg-gray-50 hover:bg-gray-100 transition-colors"
                >
                  <div className="flex items-center gap-4">
                    <span className="text-lg font-bold text-gray-400">#{index + 1}</span>
                    <div 
                      className="p-2 rounded-lg"
                      style={{ backgroundColor: `${serviceColor}20` }}
                    >
                      <Icon className="h-5 w-5" style={{ color: serviceColor }} />
                    </div>
                    <div className="text-left">
                      <h3 className="font-medium text-gray-900">{rec.finding_title}</h3>
                      <p className="text-sm text-gray-500">{rec.service_name} - {rec.resource_name || 'Multiple Resources'}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    <StatusBadge status={rec.justification_status} type="justification" />
                    {rec.estimated_monthly_savings > 0 && (
                      <span className="text-green-600 font-medium">
                        Save {formatCurrency(rec.estimated_monthly_savings)}/mo
                      </span>
                    )}
                    {isExpanded ? (
                      <ChevronUp className="h-5 w-5 text-gray-400" />
                    ) : (
                      <ChevronDown className="h-5 w-5 text-gray-400" />
                    )}
                  </div>
                </button>

                {isExpanded && (
                  <div className="p-4 border-t border-gray-200 space-y-4">
                    {rec.issue_description && (
                      <div>
                        <h4 className="text-sm font-medium text-gray-500 mb-1">Issue</h4>
                        <p className="text-gray-700">{rec.issue_description}</p>
                      </div>
                    )}
                    
                    {rec.recommendation_text && (
                      <div>
                        <h4 className="text-sm font-medium text-gray-500 mb-1">Recommendation</h4>
                        <p className="text-gray-700">{rec.recommendation_text}</p>
                      </div>
                    )}

                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 pt-4 border-t border-gray-100">
                      <div className="text-center p-3 bg-gray-50 rounded-lg">
                        <p className="text-xs text-gray-500 uppercase">Est. Savings</p>
                        <p className="text-lg font-bold text-green-600">
                          {formatCurrency(rec.estimated_monthly_savings)}
                        </p>
                        <p className="text-xs text-gray-400">per month</p>
                      </div>
                      <div className="text-center p-3 bg-gray-50 rounded-lg">
                        <p className="text-xs text-gray-500 uppercase">ROI</p>
                        <p className="text-lg font-bold text-blue-600">
                          {formatPercent(rec.roi_percentage)}
                        </p>
                        <p className="text-xs text-gray-400">return</p>
                      </div>
                      <div className="text-center p-3 bg-gray-50 rounded-lg">
                        <p className="text-xs text-gray-500 uppercase">Effort</p>
                        <p className="text-lg font-bold text-gray-700">
                          {rec.implementation_effort_hours}h
                        </p>
                        <p className="text-xs text-gray-400">to implement</p>
                      </div>
                      <div className="text-center p-3 bg-gray-50 rounded-lg">
                        <p className="text-xs text-gray-500 uppercase">Department</p>
                        <p className="text-lg font-bold text-gray-700">
                          {rec.department_name || '-'}
                        </p>
                        <p className="text-xs text-gray-400">affected</p>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
