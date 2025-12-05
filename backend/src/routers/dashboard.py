from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from typing import Optional
from src.database import get_db
from src.models import AwsCost, Department
from src.schemas import DashboardResponse

router = APIRouter()

@router.get("/api/dashboard", response_model=DashboardResponse)
def get_dashboard(
    days: int = Query(30, ge=1, le=365, description="Number of days to include"),
    db: Session = Depends(get_db)
):
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    prev_start_date = start_date - timedelta(days=days)
    
    current_costs = db.query(func.sum(AwsCost.cost)).filter(
        AwsCost.start_date >= start_date,
        AwsCost.end_date <= end_date
    ).scalar() or 0.0
    
    prev_costs = db.query(func.sum(AwsCost.cost)).filter(
        AwsCost.start_date >= prev_start_date,
        AwsCost.end_date <= start_date
    ).scalar() or 0.0
    
    cost_change = None
    if prev_costs > 0:
        cost_change = ((current_costs - prev_costs) / prev_costs) * 100
    
    top_services_query = db.query(
        AwsCost.service_name,
        func.sum(AwsCost.cost).label('total_cost'),
        func.count(func.distinct(AwsCost.resource_id)).label('resource_count')
    ).filter(
        AwsCost.start_date >= start_date,
        AwsCost.end_date <= end_date
    ).group_by(AwsCost.service_name).order_by(
        func.sum(AwsCost.cost).desc()
    ).limit(10).all()
    
    top_services = [
        {
            "service_name": s.service_name,
            "total_cost": float(s.total_cost),
            "resource_count": s.resource_count,
            "percentage": float(s.total_cost / current_costs * 100) if current_costs > 0 else 0
        }
        for s in top_services_query
    ]
    
    departments = db.query(Department).order_by(Department.total_cost.desc()).limit(10).all()
    top_departments = [
        {
            "name": d.name,
            "total_cost": float(d.total_cost),
            "budget": float(d.budget) if d.budget else None,
            "budget_utilization": float(d.total_cost / d.budget * 100) if d.budget and d.budget > 0 else None
        }
        for d in departments
    ]
    
    daily_costs = db.query(
        func.date(AwsCost.start_date).label('date'),
        func.sum(AwsCost.cost).label('daily_cost')
    ).filter(
        AwsCost.start_date >= start_date,
        AwsCost.end_date <= end_date
    ).group_by(func.date(AwsCost.start_date)).order_by(
        func.date(AwsCost.start_date)
    ).all()
    
    cost_trend = [
        {
            "date": str(dc.date),
            "cost": float(dc.daily_cost)
        }
        for dc in daily_costs
    ]
    
    return DashboardResponse(
        total_cost=float(current_costs),
        total_cost_change_percent=cost_change,
        period_start=start_date,
        period_end=end_date,
        top_services=top_services,
        top_departments=top_departments,
        cost_trend=cost_trend
    )
