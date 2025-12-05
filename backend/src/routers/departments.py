from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from src.database import get_db
from src.models import Department
from src.schemas import DepartmentSchema
from src.aws_service import aws_service

router = APIRouter()

@router.get("/api/departments", response_model=List[DepartmentSchema])
def list_departments(db: Session = Depends(get_db)):
    departments = db.query(Department).order_by(Department.total_cost.desc()).all()
    return departments

@router.get("/api/departments/{name}")
def get_department(name: str, db: Session = Depends(get_db)):
    department = db.query(Department).filter(Department.name == name).first()
    if not department:
        raise HTTPException(status_code=404, detail=f"Department '{name}' not found")
    
    return {
        "id": department.id,
        "name": department.name,
        "tag_key": department.tag_key,
        "tag_value": department.tag_value,
        "total_cost": department.total_cost,
        "budget": department.budget,
        "budget_utilization": (department.total_cost / department.budget * 100) if department.budget and department.budget > 0 else None,
        "created_at": department.created_at,
        "updated_at": department.updated_at
    }

@router.post("/api/departments/sync")
def sync_departments(
    days: int = Query(30, ge=1, le=365),
    tag_key: str = Query("Department", description="AWS tag key for department mapping"),
    db: Session = Depends(get_db)
):
    try:
        count = aws_service.sync_department_costs(db, days, tag_key)
        return {
            "status": "success",
            "message": f"Synced {count} department records",
            "tag_key": tag_key
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/api/departments/{name}/budget")
def update_department_budget(
    name: str,
    budget: float = Query(..., ge=0, description="Monthly budget amount"),
    db: Session = Depends(get_db)
):
    department = db.query(Department).filter(Department.name == name).first()
    if not department:
        raise HTTPException(status_code=404, detail=f"Department '{name}' not found")
    
    department.budget = budget
    db.commit()
    db.refresh(department)
    
    return {
        "status": "success",
        "message": f"Budget updated for department '{name}'",
        "budget": budget
    }
