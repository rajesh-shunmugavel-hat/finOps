from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class DepartmentBase(BaseModel):
    name: str
    monthly_budget: float = 0
    cost_center: Optional[str] = None

class DepartmentResponse(DepartmentBase):
    id: int
    total_cost: float = 0
    
    class Config:
        from_attributes = True

class ServiceBase(BaseModel):
    name: str
    service_type: str
    monthly_cost: float = 0
    category: Optional[str] = None

class ServiceResponse(ServiceBase):
    id: int
    percentage_of_total: float = 0
    resource_count: int = 0
    
    class Config:
        from_attributes = True

class ResourceBase(BaseModel):
    resource_name: str
    resource_type: Optional[str] = None
    instance_type: Optional[str] = None
    monthly_cost: float = 0
    region: str = "us-east-1"
    status: str = "running"

class EC2MetricResponse(BaseModel):
    cpu_utilization: float
    cpu_credit_usage: float
    memory_utilization: float
    network_in: float
    network_out: float
    disk_read_ops: float
    disk_write_ops: float
    disk_read_bytes: float
    disk_write_bytes: float
    status_check_failed: int
    timestamp: datetime
    
    class Config:
        from_attributes = True

class RDSMetricResponse(BaseModel):
    cpu_utilization: float
    database_connections: int
    free_storage_space: float
    freeable_memory: float
    read_latency: float
    write_latency: float
    read_iops: float
    write_iops: float
    network_receive_throughput: float
    network_transmit_throughput: float
    timestamp: datetime
    
    class Config:
        from_attributes = True

class S3MetricResponse(BaseModel):
    bucket_size_bytes: float
    number_of_objects: int
    all_requests: int
    get_requests: int
    put_requests: int
    delete_requests: int
    bytes_downloaded: float
    bytes_uploaded: float
    first_byte_latency: float
    errors_4xx: int
    errors_5xx: int
    timestamp: datetime
    
    class Config:
        from_attributes = True

class LambdaMetricResponse(BaseModel):
    invocations: int
    duration_avg: float
    duration_max: float
    errors: int
    throttles: int
    concurrent_executions: int
    dead_letter_errors: int
    iterator_age: float
    provisioned_concurrency_invocations: int
    timestamp: datetime
    
    class Config:
        from_attributes = True

class ResourceWithMetrics(ResourceBase):
    id: int
    service_name: str
    department_name: Optional[str] = None
    utilization_status: str = "Unknown"
    ec2_metrics: Optional[EC2MetricResponse] = None
    rds_metrics: Optional[RDSMetricResponse] = None
    s3_metrics: Optional[S3MetricResponse] = None
    lambda_metrics: Optional[LambdaMetricResponse] = None
    
    class Config:
        from_attributes = True

class ServiceDrilldown(BaseModel):
    service: ServiceResponse
    resources: List[ResourceWithMetrics]
    total_cost: float
    department_breakdown: List[dict]

class RecommendationResponse(BaseModel):
    id: int
    service_name: str
    resource_name: Optional[str]
    finding_title: str
    justification_status: str
    issue_description: Optional[str]
    recommendation_text: Optional[str]
    estimated_monthly_savings: float
    roi_percentage: float
    implementation_effort_hours: float
    department_name: Optional[str]
    
    class Config:
        from_attributes = True

class AIReportResponse(BaseModel):
    id: int
    analysis_date: datetime
    total_current_spend: float
    total_monthly_savings: float
    optimization_count: int
    status: str
    executive_summary: Optional[str]
    recommendations: List[RecommendationResponse]
    
    class Config:
        from_attributes = True

class DashboardResponse(BaseModel):
    total_monthly_spend: float
    month_over_month_change: float
    services: List[ServiceResponse]
    departments: List[DepartmentResponse]
    top_cost_drivers: List[dict]
    monthly_trend: List[dict]
    optimization_potential: float

class AnalysisRequest(BaseModel):
    service_filter: Optional[str] = None
    department_filter: Optional[str] = None

class MonthlyCostTrend(BaseModel):
    month: str
    total_cost: float
    services: dict
