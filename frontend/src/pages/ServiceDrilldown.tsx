import { useState, useEffect } from 'react'
import { useParams, Link } from 'react-router-dom'
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell
} from 'recharts'
import { ArrowLeft, Server, Database, HardDrive, Zap, Info } from 'lucide-react'
import { getServiceDrilldown, type ServiceDrilldown as ServiceDrilldownType, type Resource } from '../lib/api'
import { formatCurrency, formatBytes, formatPercent, formatNumber, SERVICE_COLORS, CHART_COLORS } from '../lib/utils'
import LoadingSpinner from '../components/LoadingSpinner'
import StatusBadge from '../components/StatusBadge'

const SERVICE_ICONS: Record<string, any> = {
  EC2: Server,
  RDS: Database,
  S3: HardDrive,
  Lambda: Zap,
}

function EC2MetricsCard({ resource }: { resource: Resource }) {
  const metrics = resource.ec2_metrics
  if (!metrics) return null

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      <div className="metric-card">
        <p className="text-sm text-gray-500">CPU Utilization</p>
        <p className="text-2xl font-bold text-gray-900">{formatPercent(metrics.cpu_utilization)}</p>
        <div className="mt-2 h-2 bg-gray-200 rounded-full overflow-hidden">
          <div 
            className="h-full bg-blue-500 rounded-full"
            style={{ width: `${Math.min(metrics.cpu_utilization, 100)}%` }}
          />
        </div>
      </div>
      <div className="metric-card">
        <p className="text-sm text-gray-500">Memory Utilization</p>
        <p className="text-2xl font-bold text-gray-900">{formatPercent(metrics.memory_utilization)}</p>
        <div className="mt-2 h-2 bg-gray-200 rounded-full overflow-hidden">
          <div 
            className="h-full bg-purple-500 rounded-full"
            style={{ width: `${Math.min(metrics.memory_utilization, 100)}%` }}
          />
        </div>
      </div>
      <div className="metric-card">
        <p className="text-sm text-gray-500">Network In</p>
        <p className="text-2xl font-bold text-gray-900">{formatBytes(metrics.network_in)}</p>
        <p className="text-xs text-gray-400 mt-1">per hour</p>
      </div>
      <div className="metric-card">
        <p className="text-sm text-gray-500">Network Out</p>
        <p className="text-2xl font-bold text-gray-900">{formatBytes(metrics.network_out)}</p>
        <p className="text-xs text-gray-400 mt-1">per hour</p>
      </div>
      <div className="metric-card">
        <p className="text-sm text-gray-500">Disk Read Ops</p>
        <p className="text-2xl font-bold text-gray-900">{formatNumber(metrics.disk_read_ops)}</p>
        <p className="text-xs text-gray-400 mt-1">operations/sec</p>
      </div>
      <div className="metric-card">
        <p className="text-sm text-gray-500">Disk Write Ops</p>
        <p className="text-2xl font-bold text-gray-900">{formatNumber(metrics.disk_write_ops)}</p>
        <p className="text-xs text-gray-400 mt-1">operations/sec</p>
      </div>
      <div className="metric-card">
        <p className="text-sm text-gray-500">CPU Credit Usage</p>
        <p className="text-2xl font-bold text-gray-900">{metrics.cpu_credit_usage.toFixed(1)}</p>
        <p className="text-xs text-gray-400 mt-1">credits/hour</p>
      </div>
      <div className="metric-card">
        <p className="text-sm text-gray-500">Status Checks</p>
        <p className={`text-2xl font-bold ${metrics.status_check_failed > 0 ? 'text-red-600' : 'text-green-600'}`}>
          {metrics.status_check_failed > 0 ? 'Failed' : 'Passed'}
        </p>
      </div>
    </div>
  )
}

function RDSMetricsCard({ resource }: { resource: Resource }) {
  const metrics = resource.rds_metrics
  if (!metrics) return null

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      <div className="metric-card">
        <p className="text-sm text-gray-500">CPU Utilization</p>
        <p className="text-2xl font-bold text-gray-900">{formatPercent(metrics.cpu_utilization)}</p>
        <div className="mt-2 h-2 bg-gray-200 rounded-full overflow-hidden">
          <div 
            className="h-full bg-blue-500 rounded-full"
            style={{ width: `${Math.min(metrics.cpu_utilization, 100)}%` }}
          />
        </div>
      </div>
      <div className="metric-card">
        <p className="text-sm text-gray-500">DB Connections</p>
        <p className="text-2xl font-bold text-gray-900">{metrics.database_connections}</p>
        <p className="text-xs text-gray-400 mt-1">active connections</p>
      </div>
      <div className="metric-card">
        <p className="text-sm text-gray-500">Free Storage</p>
        <p className="text-2xl font-bold text-gray-900">{formatBytes(metrics.free_storage_space)}</p>
        <p className="text-xs text-gray-400 mt-1">available</p>
      </div>
      <div className="metric-card">
        <p className="text-sm text-gray-500">Freeable Memory</p>
        <p className="text-2xl font-bold text-gray-900">{formatBytes(metrics.freeable_memory)}</p>
        <p className="text-xs text-gray-400 mt-1">available RAM</p>
      </div>
      <div className="metric-card">
        <p className="text-sm text-gray-500">Read Latency</p>
        <p className="text-2xl font-bold text-gray-900">{(metrics.read_latency * 1000).toFixed(2)}ms</p>
        <p className="text-xs text-gray-400 mt-1">average</p>
      </div>
      <div className="metric-card">
        <p className="text-sm text-gray-500">Write Latency</p>
        <p className="text-2xl font-bold text-gray-900">{(metrics.write_latency * 1000).toFixed(2)}ms</p>
        <p className="text-xs text-gray-400 mt-1">average</p>
      </div>
      <div className="metric-card">
        <p className="text-sm text-gray-500">Read IOPS</p>
        <p className="text-2xl font-bold text-gray-900">{formatNumber(metrics.read_iops)}</p>
        <p className="text-xs text-gray-400 mt-1">per second</p>
      </div>
      <div className="metric-card">
        <p className="text-sm text-gray-500">Write IOPS</p>
        <p className="text-2xl font-bold text-gray-900">{formatNumber(metrics.write_iops)}</p>
        <p className="text-xs text-gray-400 mt-1">per second</p>
      </div>
    </div>
  )
}

function S3MetricsCard({ resource }: { resource: Resource }) {
  const metrics = resource.s3_metrics
  if (!metrics) return null

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      <div className="metric-card">
        <p className="text-sm text-gray-500">Bucket Size</p>
        <p className="text-2xl font-bold text-gray-900">{formatBytes(metrics.bucket_size_bytes)}</p>
        <p className="text-xs text-gray-400 mt-1">total storage</p>
      </div>
      <div className="metric-card">
        <p className="text-sm text-gray-500">Objects</p>
        <p className="text-2xl font-bold text-gray-900">{formatNumber(metrics.number_of_objects)}</p>
        <p className="text-xs text-gray-400 mt-1">stored objects</p>
      </div>
      <div className="metric-card">
        <p className="text-sm text-gray-500">All Requests</p>
        <p className="text-2xl font-bold text-gray-900">{formatNumber(metrics.all_requests)}</p>
        <p className="text-xs text-gray-400 mt-1">per hour</p>
      </div>
      <div className="metric-card">
        <p className="text-sm text-gray-500">GET Requests</p>
        <p className="text-2xl font-bold text-gray-900">{formatNumber(metrics.get_requests)}</p>
        <p className="text-xs text-gray-400 mt-1">per hour</p>
      </div>
      <div className="metric-card">
        <p className="text-sm text-gray-500">PUT Requests</p>
        <p className="text-2xl font-bold text-gray-900">{formatNumber(metrics.put_requests)}</p>
        <p className="text-xs text-gray-400 mt-1">per hour</p>
      </div>
      <div className="metric-card">
        <p className="text-sm text-gray-500">Bytes Downloaded</p>
        <p className="text-2xl font-bold text-gray-900">{formatBytes(metrics.bytes_downloaded)}</p>
        <p className="text-xs text-gray-400 mt-1">per hour</p>
      </div>
      <div className="metric-card">
        <p className="text-sm text-gray-500">4xx Errors</p>
        <p className={`text-2xl font-bold ${metrics.errors_4xx > 0 ? 'text-yellow-600' : 'text-green-600'}`}>
          {metrics.errors_4xx}
        </p>
        <p className="text-xs text-gray-400 mt-1">client errors</p>
      </div>
      <div className="metric-card">
        <p className="text-sm text-gray-500">5xx Errors</p>
        <p className={`text-2xl font-bold ${metrics.errors_5xx > 0 ? 'text-red-600' : 'text-green-600'}`}>
          {metrics.errors_5xx}
        </p>
        <p className="text-xs text-gray-400 mt-1">server errors</p>
      </div>
    </div>
  )
}

function LambdaMetricsCard({ resource }: { resource: Resource }) {
  const metrics = resource.lambda_metrics
  if (!metrics) return null

  const errorRate = metrics.invocations > 0 
    ? (metrics.errors / metrics.invocations * 100) 
    : 0

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      <div className="metric-card">
        <p className="text-sm text-gray-500">Invocations</p>
        <p className="text-2xl font-bold text-gray-900">{formatNumber(metrics.invocations)}</p>
        <p className="text-xs text-gray-400 mt-1">per hour</p>
      </div>
      <div className="metric-card">
        <p className="text-sm text-gray-500">Avg Duration</p>
        <p className="text-2xl font-bold text-gray-900">{metrics.duration_avg.toFixed(0)}ms</p>
        <p className="text-xs text-gray-400 mt-1">execution time</p>
      </div>
      <div className="metric-card">
        <p className="text-sm text-gray-500">Max Duration</p>
        <p className="text-2xl font-bold text-gray-900">{metrics.duration_max.toFixed(0)}ms</p>
        <p className="text-xs text-gray-400 mt-1">peak execution</p>
      </div>
      <div className="metric-card">
        <p className="text-sm text-gray-500">Error Rate</p>
        <p className={`text-2xl font-bold ${errorRate > 5 ? 'text-red-600' : errorRate > 1 ? 'text-yellow-600' : 'text-green-600'}`}>
          {formatPercent(errorRate)}
        </p>
        <p className="text-xs text-gray-400 mt-1">{metrics.errors} errors</p>
      </div>
      <div className="metric-card">
        <p className="text-sm text-gray-500">Throttles</p>
        <p className={`text-2xl font-bold ${metrics.throttles > 0 ? 'text-orange-600' : 'text-green-600'}`}>
          {metrics.throttles}
        </p>
        <p className="text-xs text-gray-400 mt-1">throttled requests</p>
      </div>
      <div className="metric-card">
        <p className="text-sm text-gray-500">Concurrent Executions</p>
        <p className="text-2xl font-bold text-gray-900">{metrics.concurrent_executions}</p>
        <p className="text-xs text-gray-400 mt-1">simultaneous</p>
      </div>
      <div className="metric-card">
        <p className="text-sm text-gray-500">DLQ Errors</p>
        <p className={`text-2xl font-bold ${metrics.dead_letter_errors > 0 ? 'text-red-600' : 'text-green-600'}`}>
          {metrics.dead_letter_errors}
        </p>
        <p className="text-xs text-gray-400 mt-1">dead letter queue</p>
      </div>
      <div className="metric-card">
        <p className="text-sm text-gray-500">Iterator Age</p>
        <p className="text-2xl font-bold text-gray-900">{metrics.iterator_age.toFixed(0)}ms</p>
        <p className="text-xs text-gray-400 mt-1">stream lag</p>
      </div>
    </div>
  )
}

export default function ServiceDrilldown() {
  const { serviceName } = useParams<{ serviceName: string }>()
  const [data, setData] = useState<ServiceDrilldownType | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedResource, setSelectedResource] = useState<Resource | null>(null)

  useEffect(() => {
    if (serviceName) {
      loadService()
    }
  }, [serviceName])

  const loadService = async () => {
    try {
      setLoading(true)
      const serviceData = await getServiceDrilldown(serviceName!)
      setData(serviceData)
      if (serviceData.resources.length > 0) {
        setSelectedResource(serviceData.resources[0])
      }
    } catch (err) {
      setError('Failed to load service data')
      console.error(err)
    } finally {
      setLoading(false)
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
        <Link to="/" className="btn-primary mt-4 inline-block">
          Back to Dashboard
        </Link>
      </div>
    )
  }

  const Icon = SERVICE_ICONS[data.service.name] || Server
  const serviceColor = SERVICE_COLORS[data.service.name] || '#3B82F6'

  const costByResource = data.resources.map(r => ({
    name: r.resource_name.length > 15 ? r.resource_name.slice(0, 15) + '...' : r.resource_name,
    fullName: r.resource_name,
    cost: r.monthly_cost,
  })).sort((a, b) => b.cost - a.cost).slice(0, 10)

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Link
          to="/"
          className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
        >
          <ArrowLeft className="h-5 w-5 text-gray-600" />
        </Link>
        <div className="flex items-center gap-3">
          <div 
            className="p-3 rounded-xl"
            style={{ backgroundColor: `${serviceColor}20` }}
          >
            <Icon className="h-6 w-6" style={{ color: serviceColor }} />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">{data.service.name}</h1>
            <p className="text-gray-500">{data.service.service_type} Service</p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="card">
          <p className="text-sm text-gray-500">Total Monthly Cost</p>
          <p className="text-3xl font-bold text-gray-900 mt-1">{formatCurrency(data.total_cost)}</p>
          <p className="text-sm text-gray-500 mt-1">{formatPercent(data.service.percentage_of_total)} of total spend</p>
        </div>
        <div className="card">
          <p className="text-sm text-gray-500">Resources</p>
          <p className="text-3xl font-bold text-gray-900 mt-1">{data.resources.length}</p>
          <p className="text-sm text-gray-500 mt-1">active {data.service.name.toLowerCase()} resources</p>
        </div>
        <div className="card">
          <p className="text-sm text-gray-500">Avg Cost per Resource</p>
          <p className="text-3xl font-bold text-gray-900 mt-1">
            {formatCurrency(data.total_cost / Math.max(data.resources.length, 1))}
          </p>
          <p className="text-sm text-gray-500 mt-1">per month</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Cost by Resource</h2>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={costByResource} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis 
                  type="number" 
                  tick={{ fontSize: 11 }}
                  tickFormatter={(value) => `$${value}`}
                />
                <YAxis 
                  type="category" 
                  dataKey="name" 
                  tick={{ fontSize: 11 }}
                  width={120}
                />
                <Tooltip 
                  formatter={(value: number) => formatCurrency(value)}
                  labelFormatter={(label, payload) => payload?.[0]?.payload?.fullName || label}
                  contentStyle={{ borderRadius: '8px', border: '1px solid #e5e7eb' }}
                />
                <Bar dataKey="cost" fill={serviceColor} radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Cost by Department</h2>
          {data.department_breakdown.length > 0 ? (
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={data.department_breakdown}
                    cx="50%"
                    cy="50%"
                    innerRadius={50}
                    outerRadius={80}
                    paddingAngle={2}
                    dataKey="cost"
                    nameKey="department"
                    label={({ department, percent }) => `${department} (${(percent * 100).toFixed(0)}%)`}
                  >
                    {data.department_breakdown.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={CHART_COLORS[index % CHART_COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip 
                    formatter={(value: number) => formatCurrency(value)}
                    contentStyle={{ borderRadius: '8px', border: '1px solid #e5e7eb' }}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="h-64 flex items-center justify-center text-gray-500">
              No department data available
            </div>
          )}
        </div>
      </div>

      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Resources</h2>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-200">
                <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">Resource</th>
                <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">Type</th>
                <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">Department</th>
                <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">Status</th>
                <th className="text-right py-3 px-4 text-sm font-medium text-gray-500">Cost</th>
                <th className="text-center py-3 px-4 text-sm font-medium text-gray-500">Details</th>
              </tr>
            </thead>
            <tbody>
              {data.resources.map((resource) => (
                <tr 
                  key={resource.id}
                  className={`border-b border-gray-100 hover:bg-gray-50 transition-colors cursor-pointer ${
                    selectedResource?.id === resource.id ? 'bg-blue-50' : ''
                  }`}
                  onClick={() => setSelectedResource(resource)}
                >
                  <td className="py-3 px-4">
                    <p className="font-medium text-gray-900">{resource.resource_name}</p>
                    <p className="text-sm text-gray-500">{resource.region}</p>
                  </td>
                  <td className="py-3 px-4 text-sm text-gray-600">
                    {resource.instance_type || resource.resource_type}
                  </td>
                  <td className="py-3 px-4 text-sm text-gray-600">
                    {resource.department_name || '-'}
                  </td>
                  <td className="py-3 px-4">
                    <StatusBadge status={resource.utilization_status} type="utilization" />
                  </td>
                  <td className="py-3 px-4 text-right font-medium text-gray-900">
                    {formatCurrency(resource.monthly_cost)}
                  </td>
                  <td className="py-3 px-4 text-center">
                    <button 
                      className="p-1 hover:bg-gray-200 rounded transition-colors"
                      onClick={(e) => {
                        e.stopPropagation()
                        setSelectedResource(resource)
                      }}
                    >
                      <Info className="h-4 w-4 text-gray-500" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {selectedResource && (
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900">
              CloudWatch Metrics: {selectedResource.resource_name}
            </h2>
            <StatusBadge status={selectedResource.utilization_status} type="utilization" />
          </div>
          
          {data.service.name === 'EC2' && <EC2MetricsCard resource={selectedResource} />}
          {data.service.name === 'RDS' && <RDSMetricsCard resource={selectedResource} />}
          {data.service.name === 'S3' && <S3MetricsCard resource={selectedResource} />}
          {data.service.name === 'Lambda' && <LambdaMetricsCard resource={selectedResource} />}
        </div>
      )}
    </div>
  )
}
