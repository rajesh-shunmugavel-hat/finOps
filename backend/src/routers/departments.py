from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from datetime import date
from dateutil.relativedelta import relativedelta
from src.database import get_db
from src.models import AwsServiceTagCost

router = APIRouter()

def get_previous_month_range():
    first_day_this_month = date.today().replace(day=1)
    first_day_prev_month = first_day_this_month - relativedelta(months=1)
    return first_day_prev_month, first_day_this_month

@router.get("/api/departments", response_model=List[dict])
def list_departments(db: Session = Depends(get_db)):
    """List all projects/departments with total cost for previous month"""
    start_date, end_date = get_previous_month_range()

    departments_query = db.query(
        AwsServiceTagCost.tag_value.label("name"),
        func.sum(AwsServiceTagCost.cost).label("total_cost")
    ).filter(
        AwsServiceTagCost.tag_key == "Project",
        AwsServiceTagCost.activity_date >= start_date,
        AwsServiceTagCost.activity_date < end_date,
        AwsServiceTagCost.tag_value.isnot(None),
        AwsServiceTagCost.tag_value != ""
    ).group_by(AwsServiceTagCost.tag_value).all()

    # Handle missing tag values
    missing_tag_cost = db.query(func.sum(AwsServiceTagCost.cost)).filter(
        AwsServiceTagCost.tag_key == "Project",
        AwsServiceTagCost.activity_date >= start_date,
        AwsServiceTagCost.activity_date < end_date,
        (AwsServiceTagCost.tag_value.is_(None)) | (AwsServiceTagCost.tag_value == "")
    ).scalar() or 0.0

    departments = [
        {
            "id": i + 1,
            "name": d.name,
            "monthly_budget": 1000,
            "cost_center": d.name.upper().replace(" ", "_") + "-001",
            "total_cost": float(d.total_cost)
        }
        for i, d in enumerate(departments_query)
    ]

    if missing_tag_cost > 0:
        departments.append({
            "id": len(departments) + 1,
            "name": "No Tag Value",
            "monthly_budget": 1000,
            "cost_center": "NO_TAG_VALUE-001",
            "total_cost": float(missing_tag_cost)
        })

    return departments


@router.get("/api/departments/{name}")
def get_department(name: str, db: Session = Depends(get_db)):
    """Get department/project by name for previous month"""
    start_date, end_date = get_previous_month_range()

    department = db.query(
        AwsServiceTagCost.tag_value.label("name"),
        func.sum(AwsServiceTagCost.cost).label("total_cost")
    ).filter(
        AwsServiceTagCost.tag_key == "Project",
        AwsServiceTagCost.tag_value == name,
        AwsServiceTagCost.activity_date >= start_date,
        AwsServiceTagCost.activity_date < end_date
    ).group_by(AwsServiceTagCost.tag_value).first()

    if not department:
        raise HTTPException(status_code=404, detail=f"Department '{name}' not found")

    return {
        "id": 1,
        "name": department.name,
        "monthly_budget": 10000,
        "cost_center": department.name.upper().replace(" ", "_") + "-001",
        "total_cost": float(department.total_cost)
    }
