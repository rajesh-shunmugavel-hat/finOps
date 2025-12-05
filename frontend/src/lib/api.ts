import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
})

export interface Department {
  id: number
  name: string
  monthly_budget: number
  cost_center: string | null
  total_cost: number
}

export interface Service {
  id: number
  name: string
  service_type: string
  monthly_cost: number
  category: string | null
  percentage_of_total: number
  resource_count: number
}

export interface DashboardData {
  total_monthly_spend: number
  month_over_month_change: number
  services: Service[]
  departments: Department[]
  top_cost_drivers: {
    name: string
    cost: number
    percentage: number
    resource_count: number
  }[]
  monthly_trend: {
    month: string
    total_cost: number
    EC2?: number
    RDS?: number
    S3?: number
    Lambda?: number
    Other?: number
  }[]
  optimization_potential: number
}

export interface EC2Metrics {
  cpu_utilization: number
  cpu_credit_usage: number
  memory_utilization: number
  network_in: number
  network_out: number
  disk_read_ops: number
  disk_write_ops: number
  disk_read_bytes: number
  disk_write_bytes: number
  status_check_failed: number
  timestamp: string
}

export interface RDSMetrics {
  cpu_utilization: number
  database_connections: number
  free_storage_space: number
  freeable_memory: number
  read_latency: number
  write_latency: number
  read_iops: number
  write_iops: number
  network_receive_throughput: number
  network_transmit_throughput: number
  timestamp: string
}

export interface S3Metrics {
  bucket_size_bytes: number
  number_of_objects: number
  all_requests: number
  get_requests: number
  put_requests: number
  delete_requests: number
  bytes_downloaded: number
  bytes_uploaded: number
  first_byte_latency: number
  errors_4xx: number
  errors_5xx: number
  timestamp: string
}

export interface LambdaMetrics {
  invocations: number
  duration_avg: number
  duration_max: number
  errors: number
  throttles: number
  concurrent_executions: number
  dead_letter_errors: number
  iterator_age: number
  provisioned_concurrency_invocations: number
  timestamp: string
}

export interface Resource {
  id: number
  resource_name: string
  resource_type: string | null
  instance_type: string | null
  monthly_cost: number
  region: string
  status: string
  service_name: string
  department_name: string | null
  utilization_status: string
  ec2_metrics?: EC2Metrics
  rds_metrics?: RDSMetrics
  s3_metrics?: S3Metrics
  lambda_metrics?: LambdaMetrics
}

export interface ServiceDrilldown {
  service: Service
  resources: Resource[]
  total_cost: number
  department_breakdown: {
    department: string
    cost: number
  }[]
}

export interface Recommendation {
  id: number
  service_name: string
  resource_name: string | null
  finding_title: string
  justification_status: string
  issue_description: string | null
  recommendation_text: string | null
  estimated_monthly_savings: number
  roi_percentage: number
  implementation_effort_hours: number
  department_name: string | null
}

export interface AIReport {
  id: number
  analysis_date: string
  total_current_spend: number
  total_monthly_savings: number
  optimization_count: number
  status: string
  executive_summary: string | null
  recommendations: Recommendation[]
}

export const getDashboard = async (): Promise<DashboardData> => {
  const response = await api.get('/dashboard')
  return response.data
}

export const getServices = async (): Promise<Service[]> => {
  const response = await api.get('/services')
  return response.data
}

export const getServiceDrilldown = async (serviceName: string): Promise<ServiceDrilldown> => {
  const response = await api.get(`/services/${serviceName}`)
  return response.data
}

export const getResourceMetrics = async (resourceId: number) => {
  const response = await api.get(`/metrics/${resourceId}`)
  return response.data
}

export const getDepartments = async (): Promise<Department[]> => {
  const response = await api.get('/departments')
  return response.data
}

export const getDepartmentBreakdown = async (deptId: number) => {
  const response = await api.get(`/departments/${deptId}/breakdown`)
  return response.data
}

export const getReports = async (): Promise<AIReport[]> => {
  const response = await api.get('/reports')
  return response.data
}

export const getReport = async (reportId: number): Promise<AIReport> => {
  const response = await api.get(`/reports/${reportId}`)
  return response.data
}

export const triggerAnalysis = async (): Promise<AIReport> => {
  const response = await api.post('/analyze')
  return response.data
}

export default api
