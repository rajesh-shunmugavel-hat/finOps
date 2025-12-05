import { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { format } from 'date-fns'
import { FileText, Sparkles, ArrowRight, TrendingDown, Clock, AlertTriangle } from 'lucide-react'
import { getReports, triggerAnalysis, type AIReport } from '../lib/api'
import { formatCurrency, formatNumber } from '../lib/utils'
import LoadingSpinner from '../components/LoadingSpinner'
import StatusBadge from '../components/StatusBadge'

export default function Reports() {
  const navigate = useNavigate()
  const [reports, setReports] = useState<AIReport[]>([])
  const [loading, setLoading] = useState(true)
  const [analyzing, setAnalyzing] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadReports()
  }, [])

  const loadReports = async () => {
    try {
      setLoading(true)
      const data = await getReports()
      setReports(data)
    } catch (err) {
      setError('Failed to load reports')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const handleAnalyze = async () => {
    try {
      setAnalyzing(true)
      const report = await triggerAnalysis()
      navigate(`/reports/${report.id}`)
    } catch (err) {
      console.error('Analysis failed:', err)
      alert('Analysis failed. Please try again.')
    } finally {
      setAnalyzing(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">AI Analysis Reports</h1>
          <p className="text-gray-500 mt-1">History of cost optimization analyses</p>
        </div>
        <button
          onClick={handleAnalyze}
          disabled={analyzing}
          className="btn-primary flex items-center gap-2"
        >
          <Sparkles className="h-4 w-4" />
          {analyzing ? 'Generating...' : 'New Analysis'}
        </button>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
          {error}
        </div>
      )}

      {reports.length === 0 ? (
        <div className="card text-center py-12">
          <FileText className="h-12 w-12 text-gray-300 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No Reports Yet</h3>
          <p className="text-gray-500 mb-4">
            Run your first AI analysis to get cost optimization recommendations
          </p>
          <button
            onClick={handleAnalyze}
            disabled={analyzing}
            className="btn-primary inline-flex items-center gap-2"
          >
            <Sparkles className="h-4 w-4" />
            {analyzing ? 'Generating...' : 'Generate First Report'}
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          {reports.map((report) => (
            <Link
              key={report.id}
              to={`/reports/${report.id}`}
              className="card block hover:shadow-md transition-shadow group"
            >
              <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
                <div className="flex items-start gap-4">
                  <div className="p-3 bg-blue-50 rounded-xl">
                    <FileText className="h-6 w-6 text-blue-600" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <h3 className="font-semibold text-gray-900 group-hover:text-blue-600 transition-colors">
                        Analysis Report
                      </h3>
                      <span className="text-sm text-gray-500">
                        #{report.id}
                      </span>
                    </div>
                    <div className="flex items-center gap-4 text-sm text-gray-500">
                      <span className="flex items-center gap-1">
                        <Clock className="h-4 w-4" />
                        {format(new Date(report.analysis_date), 'MMM d, yyyy h:mm a')}
                      </span>
                      <span className="flex items-center gap-1">
                        <AlertTriangle className="h-4 w-4" />
                        {report.optimization_count} findings
                      </span>
                    </div>
                    {report.executive_summary && (
                      <p className="text-sm text-gray-600 mt-2 line-clamp-2">
                        {report.executive_summary}
                      </p>
                    )}
                  </div>
                </div>
                
                <div className="flex items-center gap-6">
                  <div className="grid grid-cols-2 gap-6">
                    <div className="text-center">
                      <p className="text-sm text-gray-500">Current Spend</p>
                      <p className="text-lg font-semibold text-gray-900">
                        {formatCurrency(report.total_current_spend)}
                      </p>
                    </div>
                    <div className="text-center">
                      <p className="text-sm text-gray-500">Potential Savings</p>
                      <p className="text-lg font-semibold text-green-600 flex items-center justify-center gap-1">
                        <TrendingDown className="h-4 w-4" />
                        {formatCurrency(report.total_monthly_savings)}
                      </p>
                    </div>
                  </div>
                  <ArrowRight className="h-5 w-5 text-gray-400 group-hover:text-blue-600 transition-colors" />
                </div>
              </div>

              <div className="mt-4 pt-4 border-t border-gray-100">
                <div className="flex flex-wrap gap-2">
                  {report.recommendations.slice(0, 3).map((rec) => (
                    <StatusBadge 
                      key={rec.id} 
                      status={rec.justification_status} 
                      type="justification"
                    />
                  ))}
                  {report.recommendations.length > 3 && (
                    <span className="text-sm text-gray-500">
                      +{report.recommendations.length - 3} more
                    </span>
                  )}
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  )
}
