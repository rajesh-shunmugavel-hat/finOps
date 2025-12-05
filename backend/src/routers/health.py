from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime
from src.database import get_db
from src.schemas import HealthResponse
from src.aws_service import aws_service
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/health", response_model=HealthResponse)
def health_check(db: Session = Depends(get_db)):
    db_status = "healthy"
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        db_status = "unhealthy"
    
    if not aws_service.is_configured():
        aws_status = "not_configured"
    else:
        aws_status = "healthy"
        try:
            if not aws_service.test_connection():
                aws_status = "unhealthy"
        except Exception as e:
            logger.error(f"AWS health check failed: {e}")
            aws_status = "unhealthy"
    
    overall_status = "healthy" if db_status == "healthy" else "degraded"
    
    return HealthResponse(
        status=overall_status,
        database=db_status,
        aws_connection=aws_status,
        timestamp=datetime.now()
    )
