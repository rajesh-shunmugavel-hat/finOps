import { useState, useEffect } from 'react'
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell
} from 'recharts'
import { Building2, TrendingUp, TrendingDown, DollarSign } from 'lucide-react'
import { getDepartments, getDepartmentBreakdown, type Department } from '../lib/api'
import { formatCurrency, formatPercent, CHART_COLORS } from '../lib/utils'
import LoadingSpinner from '../components/LoadingSpinner'

interface DepartmentBreakdown {
  department: string
  monthly_budget: number
  total_cost: number
  budget_variance: number
  service_breakdown: {
    service: string
    cost: number
    percentage: number
  }[]
  resources: {
    name: string
    service: string
    cost: number
    instance_type: string
  }[]
}

export default function Departments() {
  const [departments, setDepartments] = useState<Department[]>([])
  const [selectedDept, setSelectedDept] = useState<Department | null>(null)
  const [breakdown, setBreakdown] = useState<DepartmentBreakdown | null>(null)
  const [loading, setLoading] = useState(true)
  const [breakdownLoading, setBreakdownLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadDepartments()
  }, [])

  useEffect(() => {
    if (selectedDept) {
      loadBreakdown(selectedDept.id)
    }
  }, [selectedDept])

  const loadDepartments = async () => {
    try {
      setLoading(true)
      const data = await getDepartments()
      setDepartments(data)
      if (data.length > 0) {
        setSelectedDept(data[0])
      }
    } catch (err) {
      setError('Failed to load departments')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const loadBreakdown = async (deptId: number) => {
    try {
      setBreakdownLoading(true)
      const data = await getDepartmentBreakdown(deptId)
      setBreakdown(data)
    } catch (err) {
      console.error('Failed to load breakdown:', err)
    } finally {
      setBreakdownLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <LoadingSpinner size="lg" />
      </div>
    )
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <p className="text-red-600">{error}</p>
        <button onClick={loadDepartments} className="btn-primary mt-4">
          Retry
        </button>
      </div>
    )
  }

  const totalSpend = departments.reduce((sum, d) => sum + d.total_cost, 0)
  const totalBudget = departments.reduce((sum, d) => sum + d.monthly_budget, 0)
  const totalVariance = totalBudget - totalSpend

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Department Cost Analysis</h1>
        <p className="text-gray-500 mt-1">Track spending and budget allocation by team</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="card">
          <p className="text-sm text-gray-500">Total Spend</p>
          <p className="text-2xl font-bold text-gray-900 mt-1">{formatCurrency(totalSpend)}</p>
        </div>
        <div className="card">
          <p className="text-sm text-gray-500">Total Budget</p>
          <p className="text-2xl font-bold text-gray-900 mt-1">{formatCurrency(totalBudget)}</p>
        </div>
        <div className="card">
          <p className="text-sm text-gray-500">Budget Variance</p>
          <p className={`text-2xl font-bold mt-1 flex items-center gap-1 ${
            totalVariance >= 0 ? 'text-green-600' : 'text-red-600'
          }`}>
            {totalVariance >= 0 ? <TrendingDown className="h-5 w-5" /> : <TrendingUp className="h-5 w-5" />}
            {formatCurrency(Math.abs(totalVariance))}
          </p>
        </div>
        <div className="card">
          <p className="text-sm text-gray-500">Departments</p>
          <p className="text-2xl font-bold text-gray-900 mt-1">{departments.length}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="card lg:col-span-1">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Departments</h2>
          <div className="space-y-2">
            {departments.map((dept) => {
              const isSelected = selectedDept?.id === dept.id
              const variance = dept.monthly_budget - dept.total_cost
              const isOverBudget = variance < 0
              
              return (
                <button
                  key={dept.id}
                  onClick={() => setSelectedDept(dept)}
                  className={`w-full p-4 rounded-lg text-left transition-all ${
                    isSelected 
                      ? 'bg-blue-50 border-2 border-blue-500' 
                      : 'bg-gray-50 hover:bg-gray-100 border-2 border-transparent'
                  }`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <Building2 className={`h-5 w-5 ${isSelected ? 'text-blue-600' : 'text-gray-400'}`} />
                      <div>
                        <p className="font-medium text-gray-900">{dept.name}</p>
                        <p className="text-sm text-gray-500">{dept.cost_center}</p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="font-semibold text-gray-900">{formatCurrency(dept.total_cost)}</p>
                      <p className={`text-sm ${isOverBudget ? 'text-red-600' : 'text-green-600'}`}>
                        {isOverBudget ? '+' : '-'}{formatCurrency(Math.abs(variance))}
                      </p>
                    </div>
                  </div>
                  <div className="mt-2">
                    <div className="flex justify-between text-xs text-gray-500 mb-1">
                      <span>Budget usage</span>
                      <span>{formatPercent(dept.monthly_budget > 0 ? (dept.total_cost / dept.monthly_budget * 100) : 0)}</span>
                    </div>
                    <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                      <div 
                        className={`h-full rounded-full ${
                          dept.total_cost / dept.monthly_budget > 1 
                            ? 'bg-red-500' 
                            : dept.total_cost / dept.monthly_budget > 0.9 
                              ? 'bg-yellow-500' 
                              : 'bg-green-500'
                        }`}
                        style={{ width: `${Math.min((dept.total_cost / dept.monthly_budget * 100), 100)}%` }}
                      />
                    </div>
                  </div>
                </button>
              )
            })}
          </div>
        </div>

        <div className="lg:col-span-2 space-y-6">
          {breakdownLoading ? (
            <div className="card flex items-center justify-center h-64">
              <LoadingSpinner />
            </div>
          ) : breakdown ? (
            <>
              <div className="card">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">
                  {breakdown.department} - Service Breakdown
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="h-64">
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie
                          data={breakdown.service_breakdown}
                          cx="50%"
                          cy="50%"
                          innerRadius={50}
                          outerRadius={80}
                          paddingAngle={2}
                          dataKey="cost"
                          nameKey="service"
                          label={({ service, percentage }) => `${service} (${percentage.toFixed(0)}%)`}
                        >
                          {breakdown.service_breakdown.map((entry, index) => (
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
                  <div className="space-y-3">
                    {breakdown.service_breakdown.map((service, index) => (
                      <div key={service.service} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                        <div className="flex items-center gap-3">
                          <div 
                            className="w-3 h-3 rounded-full"
                            style={{ backgroundColor: CHART_COLORS[index % CHART_COLORS.length] }}
                          />
                          <span className="font-medium text-gray-700">{service.service}</span>
                        </div>
                        <div className="text-right">
                          <p className="font-semibold text-gray-900">{formatCurrency(service.cost)}</p>
                          <p className="text-sm text-gray-500">{formatPercent(service.percentage)}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              <div className="card">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">
                  {breakdown.department} - Resources
                </h2>
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b border-gray-200">
                        <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">Resource</th>
                        <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">Service</th>
                        <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">Type</th>
                        <th className="text-right py-3 px-4 text-sm font-medium text-gray-500">Cost</th>
                      </tr>
                    </thead>
                    <tbody>
                      {breakdown.resources.map((resource, index) => (
                        <tr key={index} className="border-b border-gray-100 hover:bg-gray-50">
                          <td className="py-3 px-4 font-medium text-gray-900">{resource.name}</td>
                          <td className="py-3 px-4 text-gray-600">{resource.service}</td>
                          <td className="py-3 px-4 text-gray-600">{resource.instance_type}</td>
                          <td className="py-3 px-4 text-right font-medium text-gray-900">
                            {formatCurrency(resource.cost)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </>
          ) : (
            <div className="card text-center py-12">
              <Building2 className="h-12 w-12 text-gray-300 mx-auto mb-4" />
              <p className="text-gray-500">Select a department to view details</p>
            </div>
          )}
        </div>
      </div>

      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Department Comparison</h2>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={departments}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="name" tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 12 }} tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`} />
              <Tooltip 
                formatter={(value: number, name: string) => [formatCurrency(value), name === 'total_cost' ? 'Actual Spend' : 'Budget']}
                contentStyle={{ borderRadius: '8px', border: '1px solid #e5e7eb' }}
              />
              <Bar dataKey="monthly_budget" name="Budget" fill="#E5E7EB" radius={[4, 4, 0, 0]} />
              <Bar dataKey="total_cost" name="Actual Spend" fill="#3B82F6" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  )
}
