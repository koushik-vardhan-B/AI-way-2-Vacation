from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import logging

from database import crud, schemas
from database.base import get_db
from api.auth import get_current_admin_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["🔧 Admin"])

@router.get("/stats")
async def get_system_statistics(
    db: Session = Depends(get_db),
    admin_user: schemas.UserResponse = Depends(get_current_admin_user)
):
    """Get overall system statistics (Admin only)"""
    stats = crud.get_system_stats(db)
    
    # Get popular destinations
    popular = crud.get_popular_destinations_from_plans(db, limit=10)
    
    # Get endpoint usage
    endpoint_stats = crud.get_endpoint_stats(db, days=7)
    
    return {
        "system": stats,
        "popular_destinations": [
            {"destination": dest, "count": count}
            for dest, count in popular
        ],
        "api_endpoints": [
            {
                "endpoint": endpoint,
                "requests": count,
                "avg_response_time": float(avg_time)
            }
            for endpoint, count, avg_time in endpoint_stats
        ],
        "averages": {
            "trip_duration": crud.get_average_plan_duration(db),
            "budget": crud.get_average_budget(db)
        }
    }

@router.get("/users")
async def list_all_users(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    admin_user: schemas.UserResponse = Depends(get_current_admin_user)
):
    """List all users (Admin only)"""
    # This would need a new CRUD function
    users = db.query(crud.models.User).offset(skip).limit(limit).all()
    return users

# In api/routes/admin_routes.py - temporary fix
@router.post("/cleanup/api-usage")
async def cleanup_old_api_usage(
    days: int = 90,
    db: Session = Depends(get_db),
    admin_user: schemas.UserResponse = Depends(get_current_admin_user)
):
    """Delete old API usage records (Admin only)"""
    try:
        # Temporary implementation
        from datetime import datetime, timedelta
        from sqlalchemy import text
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Delete old API usage records
        result = db.execute(
            text("DELETE FROM api_usage WHERE created_at < :cutoff_date"),
            {"cutoff_date": cutoff_date}
        )
        db.commit()
        
        deleted = result.rowcount
        return {"deleted": deleted, "older_than_days": days}
    except Exception as e:
        db.rollback()
        logger.error(f"Error in cleanup_old_api_usage: {e}")
        return {"deleted": 0, "error": str(e)}

@router.post("/cleanup/queries")
async def cleanup_old_queries(
    days: int = 90,
    db: Session = Depends(get_db),
    admin_user: schemas.UserResponse = Depends(get_current_admin_user)
):
    """Delete old query records (Admin only)"""
    try:
        # Temporary implementation
        from datetime import datetime, timedelta
        from sqlalchemy import text
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Delete old query records
        result = db.execute(
            text("DELETE FROM queries WHERE created_at < :cutoff_date"),
            {"cutoff_date": cutoff_date}
        )
        db.commit()
        

        deleted = result.rowcount
        return {"deleted": deleted, "older_than_days": days}
    except Exception as e:
        db.rollback()
        logger.error(f"Error in cleanup_old_queries: {e}")
        return {"deleted": 0, "error": str(e)}