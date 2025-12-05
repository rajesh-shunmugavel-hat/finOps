from sqlalchemy import Column, Integer, String, Float, DateTime, Text, JSON, Enum as SQLEnum, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.database import Base
import enum

class ReportStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class AwsCost(Base):
    __tablename__ = "aws_costs"
    
    id = Column(Integer, primary_key=True, index=True)
    service_name = Column(String(255), index=True, nullable=False)
    resource_id = Column(String(255), index=True, nullable=True)
    cost = Column(Float, nullable=False)
    currency = Column(String(10), default="USD")
    usage_quantity = Column(Float, nullable=True)
    usage_unit = Column(String(100), nullable=True)
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

class Metric(Base):
    __tablename__ = "metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    service_name = Column(String(255), index=True, nullable=False)
    resource_id = Column(String(255), index=True, nullable=False)
    metric_name = Column(String(255), nullable=False)
    value = Column(Float, nullable=False)
    unit = Column(String(100), nullable=True)
    timestamp = Column(DateTime, nullable=False)
    dimensions = Column(JSON, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

class Resource(Base):
    __tablename__ = "resources"
    
    id = Column(Integer, primary_key=True, index=True)
    resource_id = Column(String(255), unique=True, index=True, nullable=False)
    service_name = Column(String(255), index=True, nullable=False)
    resource_type = Column(String(255), nullable=True)
    region = Column(String(100), nullable=True)
    tags = Column(JSON, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

class Department(Base):
    __tablename__ = "departments"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, index=True, nullable=False)
    tag_key = Column(String(255), nullable=True)
    tag_value = Column(String(255), nullable=True)
    total_cost = Column(Float, default=0.0)
    budget = Column(Float, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

class Report(Base):
    __tablename__ = "reports"
    
    id = Column(Integer, primary_key=True, index=True)
    status = Column(SQLEnum(ReportStatus), default=ReportStatus.PENDING)
    scope = Column(String(255), nullable=True)
    scope_filter = Column(JSON, nullable=True)
    summary = Column(Text, nullable=True)
    recommendations = Column(JSON, nullable=True)
    raw_ai_response = Column(Text, nullable=True)
    total_cost_analyzed = Column(Float, nullable=True)
    potential_savings = Column(Float, nullable=True)
    period_start = Column(DateTime, nullable=True)
    period_end = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    completed_at = Column(DateTime, nullable=True)
