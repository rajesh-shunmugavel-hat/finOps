from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from typing import List, Optional
from src.database import get_db
from src.models import AwsCost, Metric, Resource
from src.schemas import ServiceSummary, ServiceDetail, ResourceSchema, MetricSchema
from src.aws_service import aws_service

router = APIRouter()

@router.get("/api/services", response_model=List[ServiceSummary])
def list_services(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db)
):
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    prev_start_date = start_date - timedelta(days=days)
    
    current_query = db.query(
        AwsCost.service_name,
        func.sum(AwsCost.cost).label('total_cost'),
        func.count(func.distinct(AwsCost.resource_id)).label('resource_count')
    ).filter(
        AwsCost.start_date >= start_date,
        AwsCost.end_date <= end_date
    ).group_by(AwsCost.service_name).all()
    
    prev_costs = {}
    prev_query = db.query(
        AwsCost.service_name,
        func.sum(AwsCost.cost).label('total_cost')
    ).filter(
        AwsCost.start_date >= prev_start_date,
        AwsCost.end_date <= start_date
    ).group_by(AwsCost.service_name).all()
    
    for p in prev_query:
        prev_costs[p.service_name] = float(p.total_cost)
    
    services = []
    for s in current_query:
        cost_change = None
        if s.service_name in prev_costs and prev_costs[s.service_name] > 0:
            prev_cost = prev_costs[s.service_name]
            cost_change = ((float(s.total_cost) - prev_cost) / prev_cost) * 100
        
        services.append(ServiceSummary(
            service_name=s.service_name,
            total_cost=float(s.total_cost),
            resource_count=s.resource_count,
            cost_change_percent=cost_change
        ))
    
    return sorted(services, key=lambda x: x.total_cost, reverse=True)

@router.get("/api/services/{name}", response_model=ServiceDetail)
def get_service_detail(
    name: str,
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db)
):
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    costs = db.query(AwsCost).filter(
        AwsCost.service_name == name,
        AwsCost.start_date >= start_date,
        AwsCost.end_date <= end_date
    ).all()
    
    if not costs:
        raise HTTPException(status_code=404, detail=f"Service '{name}' not found")
    
    total_cost = sum(c.cost for c in costs)
    
    resources = db.query(Resource).filter(Resource.service_name == name).all()
    
    daily_breakdown = {}
    for c in costs:
        date_key = c.start_date.strftime('%Y-%m-%d')
        if date_key not in daily_breakdown:
            daily_breakdown[date_key] = 0
        daily_breakdown[date_key] += c.cost
    
    cost_breakdown = [
        {"date": k, "cost": v}
        for k, v in sorted(daily_breakdown.items())
    ]
    
    return ServiceDetail(
        service_name=name,
        total_cost=total_cost,
        resources=[ResourceSchema.model_validate(r) for r in resources],
        cost_breakdown=cost_breakdown,
        period_start=start_date,
        period_end=end_date
    )

@router.get("/api/services/{name}/resources", response_model=List[dict])
def get_service_resources(
    name: str,
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db)
):
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    resource_costs = db.query(
        AwsCost.resource_id,
        func.sum(AwsCost.cost).label('total_cost'),
        func.sum(AwsCost.usage_quantity).label('total_usage')
    ).filter(
        AwsCost.service_name == name,
        AwsCost.start_date >= start_date,
        AwsCost.end_date <= end_date,
        AwsCost.resource_id.isnot(None)
    ).group_by(AwsCost.resource_id).all()
    
    result = []
    for rc in resource_costs:
        resource = db.query(Resource).filter(Resource.resource_id == rc.resource_id).first()
        
        result.append({
            "resource_id": rc.resource_id,
            "total_cost": float(rc.total_cost),
            "total_usage": float(rc.total_usage) if rc.total_usage else None,
            "resource_type": resource.resource_type if resource else None,
            "region": resource.region if resource else None,
            "tags": resource.tags if resource else None
        })
    
    return sorted(result, key=lambda x: x['total_cost'], reverse=True)

@router.get("/api/services/{name}/metrics")
def get_service_metrics(
    name: str,
    resource_id: Optional[str] = Query(None),
    days: int = Query(7, ge=1, le=30),
    db: Session = Depends(get_db)
):
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    query = db.query(Metric).filter(
        Metric.service_name == name,
        Metric.timestamp >= start_date,
        Metric.timestamp <= end_date
    )
    
    if resource_id:
        query = query.filter(Metric.resource_id == resource_id)
    
    metrics = query.order_by(Metric.timestamp).all()
    
    grouped_metrics = {}
    for m in metrics:
        key = f"{m.resource_id}:{m.metric_name}"
        if key not in grouped_metrics:
            grouped_metrics[key] = {
                "resource_id": m.resource_id,
                "metric_name": m.metric_name,
                "unit": m.unit,
                "data_points": []
            }
        grouped_metrics[key]["data_points"].append({
            "timestamp": m.timestamp.isoformat(),
            "value": m.value,
            "dimensions": m.dimensions
        })
    
    return {
        "service_name": name,
        "period_start": start_date.isoformat(),
        "period_end": end_date.isoformat(),
        "metrics": list(grouped_metrics.values())
    }

@router.post("/api/services/{name}/sync-metrics")
def sync_service_metrics(
    name: str,
    resource_id: str = Query(..., description="Resource ID to sync metrics for"),
    days: int = Query(7, ge=1, le=30),
    db: Session = Depends(get_db)
):
    try:
        count = aws_service.sync_metrics_for_resource(db, name, resource_id, days)
        return {
            "status": "success",
            "message": f"Synced {count} metric records for {resource_id}",
            "service_name": name,
            "resource_id": resource_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
