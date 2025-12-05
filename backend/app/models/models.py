from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum
from ..database import Base

class JustificationStatus(str, enum.Enum):
    JUSTIFIED = "JUSTIFIED"
    NOT_JUSTIFIED = "NOT_JUSTIFIED"
    PARTIALLY_JUSTIFIED = "PARTIALLY_JUSTIFIED"

class Department(Base):
    __tablename__ = "departments"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    monthly_budget = Column(Float, default=0)
    cost_center = Column(String(50))
    created_at = Column(DateTime, default=func.now())
    
    resources = relationship("Resource", back_populates="department")

class Service(Base):
    __tablename__ = "services"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False, unique=True)
    service_type = Column(String(50), nullable=False)
    monthly_cost = Column(Float, default=0)
    category = Column(String(50))
    description = Column(Text)
    created_at = Column(DateTime, default=func.now())
    
    resources = relationship("Resource", back_populates="service")

class Resource(Base):
    __tablename__ = "resources"
    
    id = Column(Integer, primary_key=True, index=True)
    service_id = Column(Integer, ForeignKey("services.id"), nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"))
    resource_name = Column(String(100), nullable=False)
    resource_type = Column(String(50))
    instance_type = Column(String(50))
    monthly_cost = Column(Float, default=0)
    region = Column(String(50), default="us-east-1")
    status = Column(String(50), default="running")
    created_at = Column(DateTime, default=func.now())
    
    service = relationship("Service", back_populates="resources")
    department = relationship("Department", back_populates="resources")
    ec2_metrics = relationship("EC2Metric", back_populates="resource", cascade="all, delete-orphan")
    rds_metrics = relationship("RDSMetric", back_populates="resource", cascade="all, delete-orphan")
    s3_metrics = relationship("S3Metric", back_populates="resource", cascade="all, delete-orphan")
    lambda_metrics = relationship("LambdaMetric", back_populates="resource", cascade="all, delete-orphan")

class EC2Metric(Base):
    __tablename__ = "ec2_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    resource_id = Column(Integer, ForeignKey("resources.id"), nullable=False)
    cpu_utilization = Column(Float, default=0)
    cpu_credit_usage = Column(Float, default=0)
    memory_utilization = Column(Float, default=0)
    network_in = Column(Float, default=0)
    network_out = Column(Float, default=0)
    disk_read_ops = Column(Float, default=0)
    disk_write_ops = Column(Float, default=0)
    disk_read_bytes = Column(Float, default=0)
    disk_write_bytes = Column(Float, default=0)
    status_check_failed = Column(Integer, default=0)
    timestamp = Column(DateTime, default=func.now())
    
    resource = relationship("Resource", back_populates="ec2_metrics")

class RDSMetric(Base):
    __tablename__ = "rds_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    resource_id = Column(Integer, ForeignKey("resources.id"), nullable=False)
    cpu_utilization = Column(Float, default=0)
    database_connections = Column(Integer, default=0)
    free_storage_space = Column(Float, default=0)
    freeable_memory = Column(Float, default=0)
    read_latency = Column(Float, default=0)
    write_latency = Column(Float, default=0)
    read_iops = Column(Float, default=0)
    write_iops = Column(Float, default=0)
    network_receive_throughput = Column(Float, default=0)
    network_transmit_throughput = Column(Float, default=0)
    timestamp = Column(DateTime, default=func.now())
    
    resource = relationship("Resource", back_populates="rds_metrics")

class S3Metric(Base):
    __tablename__ = "s3_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    resource_id = Column(Integer, ForeignKey("resources.id"), nullable=False)
    bucket_size_bytes = Column(Float, default=0)
    number_of_objects = Column(Integer, default=0)
    all_requests = Column(Integer, default=0)
    get_requests = Column(Integer, default=0)
    put_requests = Column(Integer, default=0)
    delete_requests = Column(Integer, default=0)
    bytes_downloaded = Column(Float, default=0)
    bytes_uploaded = Column(Float, default=0)
    first_byte_latency = Column(Float, default=0)
    errors_4xx = Column(Integer, default=0)
    errors_5xx = Column(Integer, default=0)
    timestamp = Column(DateTime, default=func.now())
    
    resource = relationship("Resource", back_populates="s3_metrics")

class LambdaMetric(Base):
    __tablename__ = "lambda_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    resource_id = Column(Integer, ForeignKey("resources.id"), nullable=False)
    invocations = Column(Integer, default=0)
    duration_avg = Column(Float, default=0)
    duration_max = Column(Float, default=0)
    errors = Column(Integer, default=0)
    throttles = Column(Integer, default=0)
    concurrent_executions = Column(Integer, default=0)
    dead_letter_errors = Column(Integer, default=0)
    iterator_age = Column(Float, default=0)
    provisioned_concurrency_invocations = Column(Integer, default=0)
    timestamp = Column(DateTime, default=func.now())
    
    resource = relationship("Resource", back_populates="lambda_metrics")

class AIReport(Base):
    __tablename__ = "ai_reports"
    
    id = Column(Integer, primary_key=True, index=True)
    analysis_date = Column(DateTime, default=func.now())
    total_current_spend = Column(Float, default=0)
    total_monthly_savings = Column(Float, default=0)
    optimization_count = Column(Integer, default=0)
    status = Column(String(100), default="Optimization Opportunities Found")
    executive_summary = Column(Text)
    created_at = Column(DateTime, default=func.now())
    
    recommendations = relationship("Recommendation", back_populates="report", cascade="all, delete-orphan")

class Recommendation(Base):
    __tablename__ = "recommendations"
    
    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(Integer, ForeignKey("ai_reports.id"), nullable=False)
    service_name = Column(String(50), nullable=False)
    resource_name = Column(String(100))
    finding_title = Column(String(200))
    justification_status = Column(String(50))
    issue_description = Column(Text)
    recommendation_text = Column(Text)
    estimated_monthly_savings = Column(Float, default=0)
    roi_percentage = Column(Float, default=0)
    implementation_effort_hours = Column(Float, default=0)
    department_name = Column(String(100))
    created_at = Column(DateTime, default=func.now())
    
    report = relationship("AIReport", back_populates="recommendations")

class MonthlyCostHistory(Base):
    __tablename__ = "monthly_cost_history"
    
    id = Column(Integer, primary_key=True, index=True)
    service_id = Column(Integer, ForeignKey("services.id"))
    month = Column(String(7))
    year = Column(Integer)
    total_cost = Column(Float, default=0)
    created_at = Column(DateTime, default=func.now())
