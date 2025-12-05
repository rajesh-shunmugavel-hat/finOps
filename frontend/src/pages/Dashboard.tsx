import { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { 
  PieChart, Pie, Cell, ResponsiveContainer, 
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  BarChart, Bar
} from 'recharts'
import { 
  DollarSign, TrendingUp, Sparkles, 
  Server, Database, HardDrive, Zap,
  ArrowRight, Building2
} from 'lucide-react'
import { getDashboard, triggerAnalysis, type DashboardData } from '../lib/api'
import { formatCurrency, formatPercent, SERVICE_COLORS, CHART_COLORS } from '../lib/utils'
import MetricCard from '../components/MetricCard'
import LoadingSpinner from '../components/LoadingSpinner'

const SERVICE_ICONS: Record<string, any> = {
  EC2: Server,
  RDS: Database,
  S3: HardDrive,
  Lambda: Zap,
}

export default function Dashboard() {
  const navigate = useNavigate()
  const [data, setData] = useState<DashboardData | null>(null)
  const [loading, setLoading] = useState(true)
  const [analyzing, setAnalyzing] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadDashboard()
  }, [])

  const loadDashboard = async () => {
    try {
      setLoading(true)
      const dashboardData = await getDashboard()
      setData(dashboardData)
    } catch (err) {
      setError('Failed to load dashboard data')
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

  if (error || !data) {
    return (
      <div className="text-center py-12">
        <p className="text-red-600">{error || 'Failed to load data'}</p>
        <button onClick={loadDashboard} className="btn-primary mt-4">
          Retry
        </button>
      </div>
    )
  }

  const pieData = data.services.map(s => ({
    name: s.name,
    value: s.monthly_cost,
    percentage: s.percentage_of_total,
  }))

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Cloud Cost Dashboard</h1>
          <p className="text-gray-500 mt-1">Monitor and optimize your AWS spending</p>
        </div>
        <button
          onClick={handleAnalyze}
          disabled={analyzing}
          className="btn-primary flex items-center gap-2"
        >
          <Sparkles className="h-4 w-4" />
          {analyzing ? 'Analyzing...' : 'Analyze with AI'}
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          title="Total Monthly Spend"
          value={formatCurrency(data.total_monthly_spend)}
          trend={data.month_over_month_change}
          trendLabel="vs last month"
          icon={<DollarSign className="h-5 w-5 text-blue-600" />}
        />
        <MetricCard
          title="Optimization Potential"
          value={formatCurrency(data.optimization_potential)}
          subtitle="Estimated savings available"
          icon={<TrendingUp className="h-5 w-5 text-green-600" />}
          valueClassName="text-green-600"
        />
        <MetricCard
          title="Active Services"
          value={data.services.length}
          subtitle={`${data.services.reduce((sum, s) => sum + s.resource_count, 0)} total resources`}
          icon={<Server className="h-5 w-5 text-purple-600" />}
        />
        <MetricCard
          title="Departments"
          value={data.departments.length}
          subtitle="Cost centers tracked"
          icon={<Building2 className="h-5 w-5 text-orange-600" />}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Cost by Service</h2>
          <div style={{ width: '100%', height: 256 }}>
            <ResponsiveContainer width="100%" height={256}>
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={100}
                  paddingAngle={2}
                  dataKey="value"
                  label={({ name, percentage }) => `${name} (${percentage.toFixed(0)}%)`}
                  labelLine={true}
                >
                  {pieData.map((entry, index) => (
                    <Cell 
                      key={`cell-${index}`} 
                      fill={SERVICE_COLORS[entry.name] || CHART_COLORS[index % CHART_COLORS.length]}
                      className="cursor-pointer hover:opacity-80 transition-opacity"
                      onClick={() => navigate(`/services/${entry.name.toLowerCase()}`)}
                    />
                  ))}
                </Pie>
                <Tooltip 
                  formatter={(value: number) => formatCurrency(value)}
                  contentStyle={{ borderRadius: '8px', border: '1px solid #e5e7eb' }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="mt-4 flex flex-wrap gap-3 justify-center">
            {pieData.map((entry, index) => (
              <div key={entry.name} className="flex items-center gap-2">
                <div 
                  className="w-3 h-3 rounded-full" 
                  style={{ backgroundColor: SERVICE_COLORS[entry.name] || CHART_COLORS[index % CHART_COLORS.length] }}
                />
                <span className="text-sm text-gray-600">{entry.name}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Monthly Trend</h2>
          <div style={{ width: '100%', height: 256 }}>
            <ResponsiveContainer width="100%" height={256}>
              <LineChart data={data.monthly_trend}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis 
                  dataKey="month" 
                  tick={{ fontSize: 12 }}
                  tickFormatter={(value) => {
                    const [year, month] = value.split('-')
                    return new Date(parseInt(year), parseInt(month) - 1).toLocaleDateString('en-US', { month: 'short' })
                  }}
                />
                <YAxis 
                  tick={{ fontSize: 12 }}
                  tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`}
                />
                <Tooltip 
                  formatter={(value: number) => formatCurrency(value)}
                  labelFormatter={(label) => {
                    const [year, month] = label.split('-')
                    return new Date(parseInt(year), parseInt(month) - 1).toLocaleDateString('en-US', { month: 'long', year: 'numeric' })
                  }}
                  contentStyle={{ borderRadius: '8px', border: '1px solid #e5e7eb' }}
                />
                <Legend />
                <Line 
                  type="monotone" 
                  dataKey="total_cost" 
                  name="Total"
                  stroke="#3B82F6" 
                  strokeWidth={2}
                  dot={{ fill: '#3B82F6' }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900">Top Cost Drivers</h2>
            <span className="text-sm text-gray-500">Click to drill down</span>
          </div>
          <div className="space-y-3">
            {data.top_cost_drivers.map((driver, index) => {
              const Icon = SERVICE_ICONS[driver.name] || Server
              return (
                <Link
                  key={driver.name}
                  to={`/services/${driver.name.toLowerCase()}`}
                  className="flex items-center justify-between p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors group"
                >
                  <div className="flex items-center gap-3">
                    <div 
                      className="p-2 rounded-lg"
                      style={{ backgroundColor: `${SERVICE_COLORS[driver.name]}20` }}
                    >
                      <Icon 
                        className="h-5 w-5"
                        style={{ color: SERVICE_COLORS[driver.name] }}
                      />
                    </div>
                    <div>
                      <p className="font-medium text-gray-900">{driver.name}</p>
                      <p className="text-sm text-gray-500">{driver.resource_count} resources</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    <div className="text-right">
                      <p className="font-semibold text-gray-900">{formatCurrency(driver.cost)}</p>
                      <p className="text-sm text-gray-500">{formatPercent(driver.percentage)}</p>
                    </div>
                    <ArrowRight className="h-4 w-4 text-gray-400 group-hover:text-gray-600 transition-colors" />
                  </div>
                </Link>
              )
            })}
          </div>
        </div>

        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900">Department Spending</h2>
            <Link to="/departments" className="text-sm text-blue-600 hover:text-blue-700">
              View all
            </Link>
          </div>
          <div style={{ width: '100%', height: 256 }}>
            <ResponsiveContainer width="100%" height={256}>
              <BarChart data={data.departments} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis 
                  type="number" 
                  tick={{ fontSize: 12 }}
                  tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`}
                />
                <YAxis 
                  type="category" 
                  dataKey="name" 
                  tick={{ fontSize: 12 }}
                  width={100}
                />
                <Tooltip 
                  formatter={(value: number) => formatCurrency(value)}
                  contentStyle={{ borderRadius: '8px', border: '1px solid #e5e7eb' }}
                />
                <Bar 
                  dataKey="total_cost" 
                  fill="#3B82F6"
                  radius={[0, 4, 4, 0]}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
          <div className="mt-4 grid grid-cols-2 gap-4">
            {data.departments.slice(0, 4).map((dept) => (
              <div key={dept.id} className="flex justify-between items-center text-sm">
                <span className="text-gray-600">{dept.name}</span>
                <span className="font-medium text-gray-900">{formatCurrency(dept.total_cost)}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">All Services</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {data.services.map((service) => {
            const Icon = SERVICE_ICONS[service.name] || Server
            return (
              <Link
                key={service.id}
                to={`/services/${service.name.toLowerCase()}`}
                className="p-4 border border-gray-200 rounded-lg hover:border-blue-300 hover:shadow-sm transition-all group"
              >
                <div className="flex items-center gap-3 mb-3">
                  <div 
                    className="p-2 rounded-lg"
                    style={{ backgroundColor: `${SERVICE_COLORS[service.name]}20` }}
                  >
                    <Icon 
                      className="h-5 w-5"
                      style={{ color: SERVICE_COLORS[service.name] }}
                    />
                  </div>
                  <div>
                    <p className="font-medium text-gray-900 group-hover:text-blue-600 transition-colors">
                      {service.name}
                    </p>
                    <p className="text-xs text-gray-500">{service.service_type}</p>
                  </div>
                </div>
                <div className="flex justify-between items-end">
                  <div>
                    <p className="text-xl font-bold text-gray-900">{formatCurrency(service.monthly_cost)}</p>
                    <p className="text-sm text-gray-500">{formatPercent(service.percentage_of_total)} of total</p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-medium text-gray-700">{service.resource_count}</p>
                    <p className="text-xs text-gray-500">resources</p>
                  </div>
                </div>
              </Link>
            )
          })}
        </div>
      </div>
    </div>
  )
}
