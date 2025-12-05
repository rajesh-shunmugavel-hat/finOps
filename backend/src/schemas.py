from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class ReportStatusEnum(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class AwsCostSchema(BaseModel):
    id: int
    service_name: str
    resource_id: Optional[str] = None
    cost: float
    currency: str = "USD"
    usage_quantity: Optional[float] = None
    usage_unit: Optional[str] = None
    start_date: datetime
    end_date: datetime
    metadata_json: Optional[Dict[str, Any]] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

class MetricSchema(BaseModel):
    id: int
    service_name: str
    resource_id: str
    metric_name: str
    value: float
    unit: Optional[str] = None
    timestamp: datetime
    dimensions: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True

class ResourceSchema(BaseModel):
    id: int
    resource_id: str
    service_name: str
    resource_type: Optional[str] = None
    region: Optional[str] = None
    tags: Optional[Dict[str, str]] = None
    
    class Config:
        from_attributes = True

class DepartmentSchema(BaseModel):
    id: int
    name: str
    tag_key: Optional[str] = None
    tag_value: Optional[str] = None
    total_cost: float
    budget: Optional[float] = None
    
    class Config:
        from_attributes = True

class ReportSchema(BaseModel):
    id: int
    status: ReportStatusEnum
    scope: Optional[str] = None
    scope_filter: Optional[Dict[str, Any]] = None
    summary: Optional[str] = None
    recommendations: Optional[List[Dict[str, Any]]] = None
    total_cost_analyzed: Optional[float] = None
    potential_savings: Optional[float] = None
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class ReportGenerateRequest(BaseModel):
    scope: Optional[str] = Field(None, description="Scope of the report: 'all', service name, or department name")
    scope_filter: Optional[Dict[str, Any]] = Field(None, description="Additional filters for the report")
    period_days: int = Field(30, description="Number of days to analyze", ge=1, le=365)

class DashboardResponse(BaseModel):
    total_cost: float
    total_cost_change_percent: Optional[float] = None
    period_start: datetime
    period_end: datetime
    top_services: List[Dict[str, Any]]
    # top_departments: List[Dict[str, Any]]
    cost_trend: List[Dict[str, Any]]

class ServiceSummary(BaseModel):
    service_name: str
    total_cost: float
    resource_count: int
    cost_change_percent: Optional[float] = None

class ServiceDetail(BaseModel):
    service_name: str
    total_cost: float
    resources: List[ResourceSchema]
    cost_breakdown: List[Dict[str, Any]]
    period_start: datetime
    period_end: datetime

class HealthResponse(BaseModel):
    status: str
    database: str
    aws_connection: str
    timestamp: datetime
