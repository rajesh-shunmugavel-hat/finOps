from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from typing import Optional
from src.database import get_db
from src.models import AwsService, Department, AwsService
from src.schemas import DashboardResponse
from datetime import date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import select
from dateutil.relativedelta import relativedelta

router = APIRouter()

# @router.get("/api/dashboard", response_model=DashboardResponse)
# def get_dashboard(
#     days: int = Query(30, ge=1, le=365, description="Number of days to include"),
#     db: Session = Depends(get_db)
# ):
#     first_day_prev_month = date.today().replace(day=1) - relativedelta(months=1)

    
#     # current_costs = db.query(func.sum(AwsService.cost)).filter(
#     #     AwsService.activity_date >= start_date,
#     #     AwsService.end_date <= end_date
#     # ).scalar() or 0.0
#     stmt = select(AwsService).where(AwsService.activity_date >= first_day_prev_month)
#     results = db.execute(stmt).scalars().all()

#     prev_costs = db.query(func.sum(AwsService.cost)).filter(
#         AwsService.start_date >= prev_start_date,
#         AwsService.end_date <= start_date
#     ).scalar() or 0.0
    
#     cost_change = None
#     if prev_costs > 0:
#         cost_change = ((current_costs - prev_costs) / prev_costs) * 100
    
#     top_services_query = db.query(
#         AwsService.service_name,
#         func.sum(AwsService.cost).label('total_cost'),
#         func.count(func.distinct(AwsService.resource_id)).label('resource_count')
#     ).filter(
#         AwsService.start_date >= start_date,
#         AwsService.end_date <= end_date
#     ).group_by(AwsService.service_name).order_by(
#         func.sum(AwsService.cost).desc()
#     ).limit(10).all()
    
#     top_services = [
#         {
#             "service_name": s.service_name,
#             "total_cost": float(s.total_cost),
#             "resource_count": s.resource_count,
#             "percentage": float(s.total_cost / current_costs * 100) if current_costs > 0 else 0
#         }
#         for s in top_services_query
#     ]
    
#     departments = db.query(Department).order_by(Department.total_cost.desc()).limit(10).all()
#     top_departments = [
#         {
#             "name": d.name,
#             "total_cost": float(d.total_cost),
#             "budget": float(d.budget) if d.budget else None,
#             "budget_utilization": float(d.total_cost / d.budget * 100) if d.budget and d.budget > 0 else None
#         }
#         for d in departments
#     ]
    
#     daily_costs = db.query(
#         func.date(AwsService.start_date).label('date'),
#         func.sum(AwsService.cost).label('daily_cost')
#     ).filter(
#         AwsService.start_date >= start_date,
#         AwsService.end_date <= end_date
#     ).group_by(func.date(AwsService.start_date)).order_by(
#         func.date(AwsService.start_date)
#     ).all()
    
#     cost_trend = [
#         {
#             "date": str(dc.date),
#             "cost": float(dc.daily_cost)
#         }
#         for dc in daily_costs
#     ]
    
#     return DashboardResponse(
#         total_cost=float(current_costs),
#         total_cost_change_percent=cost_change,
#         period_start=start_date,
#         period_end=end_date,
#         top_services=top_services,
#         top_departments=top_departments,
#         cost_trend=cost_trend
#     )


"""
@router.get("/api/dashboard", response_model=DashboardResponse)
def get_dashboard(
    db: Session = Depends(get_db)
):
    # 1️⃣ First day of previous month
    first_day_prev_month = date.today().replace(day=1) - relativedelta(months=1)
    first_day_this_month = date.today().replace(day=1)

    # 2️⃣ Current costs = previous month
    current_costs = db.query(func.sum(AwsService.cost)).filter(
        AwsService.activity_date >= first_day_prev_month,
        AwsService.activity_date < first_day_this_month
    ).scalar() or 0.0

    # 3️⃣ Previous month costs = month before previous
    prev_start_date = (first_day_prev_month - relativedelta(months=1))
    prev_end_date = first_day_prev_month

    prev_costs = db.query(func.sum(AwsService.cost)).filter(
        AwsService.activity_date >= prev_start_date,
        AwsService.activity_date < prev_end_date
    ).scalar() or 0.0

    cost_change = None
    if prev_costs > 0:
        cost_change = ((current_costs - prev_costs) / prev_costs) * 100

    # 4️⃣ Top services for previous month
    top_services_query = db.query(
        AwsService.service_name,
        func.sum(AwsService.cost).label('total_cost'),
        func.count(func.distinct(AwsService.id)).label('resource_count')
    ).filter(
        AwsService.activity_date >= first_day_prev_month,
        AwsService.activity_date < first_day_this_month
    ).group_by(AwsService.service_name).order_by(
        func.sum(AwsService.cost).desc()
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

    # # 5️⃣ Departments (assuming Department.total_cost exists)
    # departments = db.query(Department).order_by(Department.total_cost.desc()).limit(10).all()
    # top_departments = [
    #     {
    #         "name": d.name,
    #         "total_cost": float(d.total_cost),
    #         "budget": float(d.budget) if d.budget else None,
    #         "budget_utilization": float(d.total_cost / d.budget * 100) if d.budget and d.budget > 0 else None
    #     }
    #     for d in departments
    # ]

    # 6️⃣ Daily costs trend for previous month
    daily_costs = db.query(
        func.date(AwsService.activity_date).label('date'),
        func.sum(AwsService.cost).label('daily_cost')
    ).filter(
        AwsService.activity_date >= first_day_prev_month,
        AwsService.activity_date < first_day_this_month
    ).group_by(func.date(AwsService.activity_date)).order_by(
        func.date(AwsService.activity_date)
    ).all()

    cost_trend = [
        {
            "date": str(dc.date),
            "cost": float(dc.daily_cost)
        }
        for dc in daily_costs
    ]

    # return DashboardResponse(
    #     total_cost=float(current_costs),
    #     total_cost_change_percent=cost_change,
    #     period_start=first_day_prev_month,
    #     period_end=first_day_this_month - relativedelta(days=1),
    #     top_services=top_services,
    #     # top_departments=top_departments,
    #     cost_trend=cost_trend
    # )
    return DashboardResponse(
        total_cost=float(current_costs),
        total_cost_change_percent=cost_change,
        period_start=first_day_prev_month,
        period_end=first_day_this_month - relativedelta(days=1),
        top_services=top_services,
        # top_departments=top_departments,
        cost_trend=cost_trend
    )
"""

@router.get("/api/dashboard", response_model=dict)
def get_dashboard(db: Session = Depends(get_db)):
    from sqlalchemy import func
    from dateutil.relativedelta import relativedelta
    from datetime import date

    # 1️⃣ Define dates
    first_day_prev_month = date.today().replace(day=1) - relativedelta(months=1)
    first_day_this_month = date.today().replace(day=1)
    prev_start_date = first_day_prev_month - relativedelta(months=1)
    prev_end_date = first_day_prev_month

    # 2️⃣ Current and previous month costs
    current_costs = db.query(func.sum(AwsService.cost)).filter(
        AwsService.activity_date >= first_day_prev_month,
        AwsService.activity_date < first_day_this_month
    ).scalar() or 0.0

    prev_costs = db.query(func.sum(AwsService.cost)).filter(
        AwsService.activity_date >= prev_start_date,
        AwsService.activity_date < prev_end_date
    ).scalar() or 0.0

    month_over_month_change = None
    if prev_costs > 0:
        month_over_month_change = ((current_costs - prev_costs) / prev_costs) * 100

    # 3️⃣ Services
    services_query = db.query(
        AwsService.id,
        AwsService.service_name,
        func.sum(AwsService.cost).label('monthly_cost'),
        func.count(func.distinct(AwsService.id)).label('resource_count')
    ).filter(
        AwsService.activity_date >= first_day_prev_month,
        AwsService.activity_date < first_day_this_month
    ).group_by(AwsService.id, AwsService.service_name).all()

    services = [
        {
            "id": s.id,
            "name": s.service_name,
            "monthly_cost": float(s.monthly_cost),
            "percentage_of_total": float(s.monthly_cost / current_costs * 100) if current_costs else 0,
            "resource_count": s.resource_count
        }
        for s in services_query
    ]

    # 4️⃣ Top cost drivers (top 3 by monthly_cost)
    top_services = sorted(services, key=lambda x: x["monthly_cost"], reverse=True)[:3]
    top_cost_drivers = [
        {
            "name": s["name"],
            "cost": s["monthly_cost"],
            "percentage": s["percentage_of_total"],
            "resource_count": s["resource_count"]
        }
        for s in top_services
    ]

    # 5️⃣ Monthly trend (last 5 months)
    monthly_trend = []
    for i in range(5, 0, -1):
        month_start = first_day_this_month - relativedelta(months=i)
        month_end = (month_start + relativedelta(months=1))
        
        month_costs = db.query(
            AwsService.service_name,
            func.sum(AwsService.cost).label('monthly_cost')
        ).filter(
            AwsService.activity_date >= month_start,
            AwsService.activity_date < month_end
        ).group_by(AwsService.service_name).all()
        
        month_data = {"month": month_start.strftime("%Y-%m"), "total_cost": 0.0}
        total_cost = 0.0
        for mc in month_costs:
            month_data[mc.service_name] = float(mc.monthly_cost)
            total_cost += float(mc.monthly_cost)
        month_data["total_cost"] = total_cost
        monthly_trend.append(month_data)

    # 6️⃣ Return the new format
    return {
        "total_monthly_spend": float(current_costs),
        "month_over_month_change": float(month_over_month_change or 0),
        "optimization_potential": 0,  # hardcoded for now
        "services": services,
        "top_cost_drivers": top_cost_drivers,
        "monthly_trend": monthly_trend
    }

