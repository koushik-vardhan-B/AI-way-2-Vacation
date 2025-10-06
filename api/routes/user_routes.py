from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import logging

from database import crud, schemas
from database.base import get_db
from api.auth import get_current_active_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["👤 User Dashboard"])

@router.get("/me/stats", response_model=schemas.UserStatsResponse)
async def get_my_statistics(
    db: Session = Depends(get_db),
    current_user: schemas.UserResponse = Depends(get_current_active_user)
):
    """Get your account statistics"""
    stats = crud.get_user_stats(db, user_id=current_user.id)
    
    return schemas.UserStatsResponse(
        total_plans=stats['total_plans'],
        total_queries=stats['total_queries'],
        favorite_destinations=stats['total_favorites'],
        member_since=stats['member_since']
    )

@router.get("/me/history", response_model=List[schemas.QueryResponse])
async def get_my_query_history(
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: schemas.UserResponse = Depends(get_current_active_user)
):
    """Get your search history"""
    queries = crud.get_user_queries(db, user_id=current_user.id, limit=limit)
    return queries

@router.get("/me/api-usage")
async def get_my_api_usage(
    days: int = 7,
    db: Session = Depends(get_db),
    current_user: schemas.UserResponse = Depends(get_current_active_user)
):
    """Get your API usage for last N days"""
    usage = crud.get_user_api_usage(db, user_id=current_user.id, days=days)
    
    return {
        "total_requests": len(usage),
        "days": days,
        "requests": [
            {
                "endpoint": u.endpoint,
                "method": u.method,
                "status_code": u.status_code,
                "timestamp": u.created_at
            }
            for u in usage
        ]
    }
