from fastapi import APIRouter, Depends, Query, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List, Optional
from src.database import get_db
from src.models import Report, ReportStatus, AwsCost, Metric
from src.schemas import ReportSchema, ReportGenerateRequest
from src.openai_service import openai_service

router = APIRouter()

def generate_report_async(db_session_maker, report_id: int, scope: str, period_days: int):
    db = db_session_maker()
    try:
        if not openai_service.is_configured():
            report = db.query(Report).filter(Report.id == report_id).first()
            if report:
                report.status = ReportStatus.FAILED
                report.raw_ai_response = "OpenAI API key not configured. Please set OPENAI_API_KEY environment variable."
                db.commit()
            return
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=period_days)
        
        cost_query = db.query(AwsCost).filter(
            AwsCost.start_date >= start_date,
            AwsCost.end_date <= end_date
        )
        
        if scope and scope != "all":
            cost_query = cost_query.filter(AwsCost.service_name == scope)
        
        costs = cost_query.all()
        cost_data = [
            {
                "service_name": c.service_name,
                "resource_id": c.resource_id,
                "cost": c.cost,
                "usage_quantity": c.usage_quantity,
                "usage_unit": c.usage_unit,
                "start_date": c.start_date.isoformat(),
                "end_date": c.end_date.isoformat()
            }
            for c in costs
        ]
        
        metrics_query = db.query(Metric).filter(
            Metric.timestamp >= start_date,
            Metric.timestamp <= end_date
        )
        
        if scope and scope != "all":
            metrics_query = metrics_query.filter(Metric.service_name == scope)
        
        metrics = metrics_query.all()
        metrics_data = [
            {
                "service_name": m.service_name,
                "resource_id": m.resource_id,
                "metric_name": m.metric_name,
                "value": m.value,
                "unit": m.unit,
                "timestamp": m.timestamp.isoformat()
            }
            for m in metrics
        ]
        
        openai_service.generate_cost_optimization_report(
            db, report_id, cost_data, metrics_data, scope
        )
    except Exception as e:
        report = db.query(Report).filter(Report.id == report_id).first()
        if report:
            report.status = ReportStatus.FAILED
            report.raw_ai_response = str(e)
            db.commit()
    finally:
        db.close()

@router.get("/api/reports", response_model=List[ReportSchema])
def list_reports(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    query = db.query(Report)
    
    if status:
        try:
            status_enum = ReportStatus(status)
            query = query.filter(Report.status == status_enum)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
    
    reports = query.order_by(Report.created_at.desc()).offset(offset).limit(limit).all()
    return reports

@router.get("/api/reports/{report_id}", response_model=ReportSchema)
def get_report(report_id: int, db: Session = Depends(get_db)):
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail=f"Report {report_id} not found")
    return report

@router.get("/api/reports/{report_id}/full")
def get_report_full(report_id: int, db: Session = Depends(get_db)):
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail=f"Report {report_id} not found")
    
    return {
        "id": report.id,
        "status": report.status.value,
        "scope": report.scope,
        "scope_filter": report.scope_filter,
        "summary": report.summary,
        "recommendations": report.recommendations,
        "raw_ai_response": report.raw_ai_response,
        "total_cost_analyzed": report.total_cost_analyzed,
        "potential_savings": report.potential_savings,
        "period_start": report.period_start,
        "period_end": report.period_end,
        "created_at": report.created_at,
        "completed_at": report.completed_at
    }

@router.post("/api/reports/generate")
def generate_report(
    request: ReportGenerateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    from src.database import SessionLocal
    
    if not openai_service.is_configured():
        raise HTTPException(
            status_code=503,
            detail="OpenAI API is not configured. Please set OPENAI_API_KEY environment variable to enable AI report generation."
        )
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=request.period_days)
    
    report = Report(
        status=ReportStatus.PENDING,
        scope=request.scope or "all",
        scope_filter=request.scope_filter,
        period_start=start_date,
        period_end=end_date
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    
    background_tasks.add_task(
        generate_report_async,
        SessionLocal,
        report.id,
        request.scope or "all",
        request.period_days
    )
    
    return {
        "status": "accepted",
        "message": "Report generation started",
        "report_id": report.id,
        "scope": request.scope or "all",
        "period_days": request.period_days
    }

@router.delete("/api/reports/{report_id}")
def delete_report(report_id: int, db: Session = Depends(get_db)):
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail=f"Report {report_id} not found")
    
    db.delete(report)
    db.commit()
    
    return {"status": "success", "message": f"Report {report_id} deleted"}
