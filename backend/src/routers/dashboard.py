from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date
from dateutil.relativedelta import relativedelta
from src.database import get_db
from src.models import AwsService, AwsServiceTagCost

router = APIRouter()

@router.get("/api/dashboard", response_model=dict)
def get_dashboard(db: Session = Depends(get_db)):
    # 1️⃣ Define date ranges
    first_day_this_month = date.today().replace(day=1)
    first_day_prev_month = first_day_this_month - relativedelta(months=1)
    prev_start_date = first_day_prev_month - relativedelta(months=1)
    prev_end_date = first_day_prev_month

    # 2️⃣ Total costs
    current_costs = db.query(func.sum(AwsService.cost)).filter(
        AwsService.activity_date >= first_day_prev_month,
        AwsService.activity_date < first_day_this_month
    ).scalar() or 0.0

    prev_costs = db.query(func.sum(AwsService.cost)).filter(
        AwsService.activity_date >= prev_start_date,
        AwsService.activity_date < prev_end_date
    ).scalar() or 0.0

    month_over_month_change = ((current_costs - prev_costs) / prev_costs * 100) if prev_costs > 0 else 0.0
    optimization_potential = current_costs * 0.2  # Example: 20% of total spend

    # 3️⃣ Services aggregation
    services_query = db.query(
        AwsService.id,
        AwsService.service_name,
        func.sum(AwsService.cost).label("monthly_cost"),
        func.count(func.distinct(AwsService.id)).label("resource_count")
    ).filter(
        AwsService.activity_date >= first_day_prev_month,
        AwsService.activity_date < first_day_this_month
    ).group_by(AwsService.id, AwsService.service_name).all()

    services = [
        {
            "id": s.id,
            "name": s.service_name.split(" - ")[0],
            "service_type": s.service_name.split(" - ")[1] if " - " in s.service_name else "Various",
            "monthly_cost": float(s.monthly_cost),
            "category": "Core" if "EC2" in s.service_name or "RDS" in s.service_name else "Other",
            "percentage_of_total": float(s.monthly_cost / current_costs * 100) if current_costs else 0,
            "resource_count": s.resource_count
        }
        for s in services_query
    ]

    # 4️⃣ Top cost drivers (top 3 by monthly cost)
    top_cost_drivers = sorted(
        [
            {
                "name": s["name"],
                "cost": s["monthly_cost"],
                "percentage": s["percentage_of_total"],
                "resource_count": s["resource_count"]
            }
            for s in services
        ],
        key=lambda x: x["cost"], reverse=True
    )[:3]

    # 5️⃣ Departments/Projects aggregation (previous month only)
    departments_query = (
        db.query(
            AwsServiceTagCost.tag_value.label("name"),
            func.sum(AwsServiceTagCost.cost).label("total_cost")
        )
        .filter(
            AwsServiceTagCost.tag_key == "Project",
            AwsServiceTagCost.activity_date >= first_day_prev_month,
            AwsServiceTagCost.activity_date < first_day_this_month,  # only previous month
            AwsServiceTagCost.tag_value.isnot(None),
            AwsServiceTagCost.tag_value != ""
        )
        .group_by(AwsServiceTagCost.tag_value)
        .all()
    )

    # Handle missing tag values separately for previous month
    missing_tag_cost = (
        db.query(func.sum(AwsServiceTagCost.cost))
        .filter(
            AwsServiceTagCost.tag_key == "Project",
            AwsServiceTagCost.activity_date >= first_day_prev_month,
            AwsServiceTagCost.activity_date < first_day_this_month,  # only previous month
            (AwsServiceTagCost.tag_value.is_(None)) | (AwsServiceTagCost.tag_value == "")
        )
        .scalar()
        or 0.0
    )

    # Prepare final departments list
    departments = [
        {
            "id": i + 1,
            "name": d.name,
            "monthly_budget": 1000,  # Replace if you have actual mapping
            "cost_center": d.name.upper().replace(" ", "_") + "-001",
            "total_cost": float(d.total_cost)
        }
        for i, d in enumerate(departments_query)
    ]

    # 6️⃣ Monthly trend (last 5 months)
    monthly_trend = []
    for i in range(5, 0, -1):
        month_start = first_day_this_month - relativedelta(months=i)
        month_end = month_start + relativedelta(months=1)

        month_costs = db.query(
            AwsService.service_name,
            func.sum(AwsService.cost).label("monthly_cost")
        ).filter(
            AwsService.activity_date >= month_start,
            AwsService.activity_date < month_end
        ).group_by(AwsService.service_name).all()

        month_data = {"month": month_start.strftime("%Y-%m"), "total_cost": 0.0}
        total_cost = 0.0
        for mc in month_costs:
            service_name_key = mc.service_name.split(" - ")[0]
            month_data[service_name_key] = float(mc.monthly_cost)
            total_cost += float(mc.monthly_cost)
        month_data["total_cost"] = total_cost
        monthly_trend.append(month_data)

    # 7️⃣ Return final dashboard
    return {
        "total_monthly_spend": float(current_costs),
        "month_over_month_change": float(month_over_month_change),
        "optimization_potential": float(optimization_potential),
        "services": services,
        "departments": departments,
        "top_cost_drivers": top_cost_drivers,
        "monthly_trend": monthly_trend
    }
