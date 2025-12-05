from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from ..database import get_db
from ..models.models import Department, Resource, Service
from ..models.schemas import DepartmentResponse

router = APIRouter(prefix="/api", tags=["departments"])

@router.get("/departments", response_model=List[DepartmentResponse])
def get_all_departments(db: Session = Depends(get_db)):
    departments = db.query(Department).all()
    
    result = []
    for dept in departments:
        total_cost = db.query(func.sum(Resource.monthly_cost)).filter(
            Resource.department_id == dept.id
        ).scalar() or 0
        
        result.append(DepartmentResponse(
            id=dept.id,
            name=dept.name,
            monthly_budget=dept.monthly_budget,
            cost_center=dept.cost_center,
            total_cost=round(total_cost, 2)
        ))
    
    return result

@router.get("/departments/{dept_id}/breakdown")
def get_department_breakdown(dept_id: int, db: Session = Depends(get_db)):
    department = db.query(Department).filter(Department.id == dept_id).first()
    
    if not department:
        return {"error": "Department not found"}
    
    resources = db.query(Resource).filter(Resource.department_id == dept_id).all()
    
    service_costs = {}
    for resource in resources:
        service = db.query(Service).filter(Service.id == resource.service_id).first()
        if service:
            if service.name not in service_costs:
                service_costs[service.name] = 0
            service_costs[service.name] += resource.monthly_cost
    
    total_cost = sum(service_costs.values())
    
    return {
        "department": department.name,
        "monthly_budget": department.monthly_budget,
        "total_cost": round(total_cost, 2),
        "budget_variance": round(department.monthly_budget - total_cost, 2),
        "service_breakdown": [
            {
                "service": name,
                "cost": round(cost, 2),
                "percentage": round((cost / total_cost * 100), 1) if total_cost > 0 else 0
            }
            for name, cost in service_costs.items()
        ],
        "resources": [
            {
                "name": r.resource_name,
                "service": db.query(Service).filter(Service.id == r.service_id).first().name,
                "cost": r.monthly_cost,
                "instance_type": r.instance_type
            }
            for r in resources
        ]
    }
