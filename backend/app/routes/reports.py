from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..models.models import AIReport, Recommendation
from ..models.schemas import AIReportResponse, RecommendationResponse, AnalysisRequest
from ..services.ai_service import generate_ai_analysis

router = APIRouter(prefix="/api", tags=["reports"])

@router.get("/reports", response_model=List[AIReportResponse])
def get_all_reports(db: Session = Depends(get_db)):
    reports = db.query(AIReport).order_by(AIReport.analysis_date.desc()).all()
    
    result = []
    for report in reports:
        recommendations = db.query(Recommendation).filter(
            Recommendation.report_id == report.id
        ).all()
        
        result.append(AIReportResponse(
            id=report.id,
            analysis_date=report.analysis_date,
            total_current_spend=report.total_current_spend,
            total_monthly_savings=report.total_monthly_savings,
            optimization_count=report.optimization_count,
            status=report.status,
            executive_summary=report.executive_summary,
            recommendations=[
                RecommendationResponse(
                    id=rec.id,
                    service_name=rec.service_name,
                    resource_name=rec.resource_name,
                    finding_title=rec.finding_title,
                    justification_status=rec.justification_status,
                    issue_description=rec.issue_description,
                    recommendation_text=rec.recommendation_text,
                    estimated_monthly_savings=rec.estimated_monthly_savings,
                    roi_percentage=rec.roi_percentage,
                    implementation_effort_hours=rec.implementation_effort_hours,
                    department_name=rec.department_name
                )
                for rec in recommendations
            ]
        ))
    
    return result

@router.get("/reports/{report_id}", response_model=AIReportResponse)
def get_report(report_id: int, db: Session = Depends(get_db)):
    report = db.query(AIReport).filter(AIReport.id == report_id).first()
    
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    
    recommendations = db.query(Recommendation).filter(
        Recommendation.report_id == report.id
    ).all()
    
    return AIReportResponse(
        id=report.id,
        analysis_date=report.analysis_date,
        total_current_spend=report.total_current_spend,
        total_monthly_savings=report.total_monthly_savings,
        optimization_count=report.optimization_count,
        status=report.status,
        executive_summary=report.executive_summary,
        recommendations=[
            RecommendationResponse(
                id=rec.id,
                service_name=rec.service_name,
                resource_name=rec.resource_name,
                finding_title=rec.finding_title,
                justification_status=rec.justification_status,
                issue_description=rec.issue_description,
                recommendation_text=rec.recommendation_text,
                estimated_monthly_savings=rec.estimated_monthly_savings,
                roi_percentage=rec.roi_percentage,
                implementation_effort_hours=rec.implementation_effort_hours,
                department_name=rec.department_name
            )
            for rec in recommendations
        ]
    )

@router.post("/analyze", response_model=AIReportResponse)
def trigger_analysis(request: AnalysisRequest = None, db: Session = Depends(get_db)):
    try:
        report = generate_ai_analysis(db)
        
        recommendations = db.query(Recommendation).filter(
            Recommendation.report_id == report.id
        ).all()
        
        return AIReportResponse(
            id=report.id,
            analysis_date=report.analysis_date,
            total_current_spend=report.total_current_spend,
            total_monthly_savings=report.total_monthly_savings,
            optimization_count=report.optimization_count,
            status=report.status,
            executive_summary=report.executive_summary,
            recommendations=[
                RecommendationResponse(
                    id=rec.id,
                    service_name=rec.service_name,
                    resource_name=rec.resource_name,
                    finding_title=rec.finding_title,
                    justification_status=rec.justification_status,
                    issue_description=rec.issue_description,
                    recommendation_text=rec.recommendation_text,
                    estimated_monthly_savings=rec.estimated_monthly_savings,
                    roi_percentage=rec.roi_percentage,
                    implementation_effort_hours=rec.implementation_effort_hours,
                    department_name=rec.department_name
                )
                for rec in recommendations
            ]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")
