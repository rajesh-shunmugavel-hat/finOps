from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from src.database import get_db
from src.aws_service import aws_service

router = APIRouter()

@router.post("/api/sync/costs")
def sync_costs(
    days: int = Query(30, ge=1, le=365, description="Number of days to sync"),
    db: Session = Depends(get_db)
):
    if not aws_service.is_configured():
        raise HTTPException(
            status_code=503,
            detail="AWS credentials not configured. Please set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables."
        )
    
    try:
        count = aws_service.sync_cost_data(db, days)
        return {
            "status": "success",
            "message": f"Synced {count} cost records",
            "days": days
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/sync/all")
def sync_all(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db)
):
    if not aws_service.is_configured():
        raise HTTPException(
            status_code=503,
            detail="AWS credentials not configured. Please set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables."
        )
    
    results = {
        "costs": None,
        "departments": None,
        "errors": []
    }
    
    try:
        cost_count = aws_service.sync_cost_data(db, days)
        results["costs"] = f"Synced {cost_count} records"
    except Exception as e:
        results["errors"].append(f"Cost sync failed: {str(e)}")
    
    try:
        dept_count = aws_service.sync_department_costs(db, days)
        results["departments"] = f"Synced {dept_count} records"
    except Exception as e:
        results["errors"].append(f"Department sync failed: {str(e)}")
    
    status = "success" if not results["errors"] else "partial"
    return {
        "status": status,
        "results": results,
        "days": days
    }
