from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import List, Dict, Any
from datetime import datetime, timedelta

from src.database import get_db
from src.models import Report, ReportStatus, AwsCost, Metric
from src.gemini_service import gemini_service
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

class CostDataItem(BaseModel):
    service_name: str
    resource_id: str
    cost: float
    usage_quantity: float
    usage_unit: str
    start_date: str
    end_date: str

class MetricDataItem(BaseModel):
    service_name: str
    resource_id: str
    metric_name: str
    value: float
    unit: str
    timestamp: str

class TestReportPayload(BaseModel):
    cost_data: List[CostDataItem]
    metrics_data: List[MetricDataItem]
    scope: str = "all"

class DirectRecommendationPayload(BaseModel):
    resource_id: str = Field(..., description="The specific resource ID to analyze (e.g., an instance ID, bucket name).")
    service_name: str = Field(..., description="The AWS service the resource belongs to (e.g., 'AmazonEC2').")

@router.post("/api/debug/generate-test-report", tags=["Debug"])
def generate_test_report(payload: TestReportPayload, db: Session = Depends(get_db)):
    """
    A debug endpoint to directly call the Gemini service with custom data and see the raw output.
    This creates a temporary report and cleans it up afterwards.
    """
    if not gemini_service.is_configured():
        raise HTTPException(
            status_code=503,
            detail="Gemini API is not configured. Please set GEMINI_API_KEY."
        )

    temp_report = Report(
        status=ReportStatus.PENDING,
        scope=f"debug-{payload.scope}",
        period_start=datetime.now() - timedelta(days=1),
        period_end=datetime.now()
    )
    db.add(temp_report)
    db.commit()
    db.refresh(temp_report)
    report_id = temp_report.id
    
    logger.info(f"Created temporary debug report with ID: {report_id}")

    try:
        # Convert Pydantic models to dictionaries for the service
        cost_data_dicts = [item.dict() for item in payload.cost_data]
        metrics_data_dicts = [item.dict() for item in payload.metrics_data]

        response = gemini_service.generate_cost_optimization_report(
            db=db,
            report_id=report_id,
            cost_data=cost_data_dicts,
            metrics_data=metrics_data_dicts,
            scope=payload.scope
        )
        return response
    except Exception as e:
        logger.error(f"Error in debug report generation for report {report_id}: {e}")
        # The service itself will set the report to FAILED, but we raise an HTTP error
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Clean up the temporary report
        report_to_delete = db.query(Report).filter(Report.id == report_id).first()
        if report_to_delete:
            logger.info(f"Cleaning up temporary debug report with ID: {report_id}")
            db.delete(report_to_delete)
            db.commit()

@router.post("/api/debug/direct-recommendation", tags=["Debug"])
def get_direct_recommendation(payload: DirectRecommendationPayload, db: Session = Depends(get_db)):
    """
    A simplified endpoint to get a direct recommendation for a single resource
    without creating a persistent report.
    """
    if not gemini_service.is_configured():
        raise HTTPException(
            status_code=503,
            detail="Gemini API is not configured. Please set GEMINI_API_KEY."
        )

    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)

    # 1. Get Cost Data for the specific resource
    costs = db.query(AwsCost).filter(
        AwsCost.resource_id == payload.resource_id,
        AwsCost.start_date >= start_date
    ).order_by(AwsCost.start_date.desc()).all()
    
    cost_data_dicts = [{
        "service_name": c.service_name,
        "resource_id": c.resource_id,
        "cost": c.cost,
        "usage_quantity": c.usage_quantity,
        "usage_unit": c.usage_unit,
        "start_date": c.start_date.isoformat(),
        "end_date": c.end_date.isoformat()
    } for c in costs]

    # 2. Get Metrics Data for the specific resource
    metrics = db.query(Metric).filter(
        Metric.resource_id == payload.resource_id,
        Metric.timestamp >= start_date
    ).order_by(Metric.timestamp.desc()).all()
    
    metrics_data_dicts = [{
        "service_name": m.service_name,
        "resource_id": m.resource_id,
        "metric_name": m.metric_name,
        "value": m.value,
        "unit": m.unit,
        "timestamp": m.timestamp.isoformat()
    } for m in metrics]

    # 3. Get basic service info (could be expanded)
    service_info = {
        "service_name": payload.service_name,
        "resource_id": payload.resource_id
    }

    # 4. Pass to Gemini to get the recommendation
    recommendation = gemini_service.get_direct_recommendation(
        cost_data=cost_data_dicts,
        metrics_data=metrics_data_dicts,
        service_info=service_info
    )

    return {"recommendation": recommendation}


# Example payload for the endpoint:
# {
#   "cost_data": [
#     {
#       "service_name": "AmazonEC2",
#       "resource_id": "i-0abcdef1234567890",
#       "cost": 150.75,
#       "usage_quantity": 720.0,
#       "usage_unit": "Hours",
#       "start_date": "2024-05-01T00:00:00Z",
#       "end_date": "2024-05-31T23:59:59Z"
#     }
#   ],
#   "metrics_data": [
#     {
#       "service_name": "AmazonEC2",
#       "resource_id": "i-0abcdef1234567890",
#       "metric_name": "CPUUtilization",
#       "value": 15.5,
#       "unit": "Percent",
#       "timestamp": "2024-05-30T12:00:00Z"
#     }
#   ],
#   "scope": "AmazonEC2"
# }
