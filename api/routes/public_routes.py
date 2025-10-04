from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
import logging

from database import crud, schemas
from database.base import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/public", tags=["🌍 Public"])

@router.get("/popular-destinations", response_model=List[schemas.PopularDestinationResponse])
async def get_popular_destinations(
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """Get most popular destinations (no auth required)"""
    popular = crud.get_popular_destinations_from_plans(db, limit=limit)
    
    return [
        schemas.PopularDestinationResponse(destination=dest, count=count)
        for dest, count in popular
    ]

@router.get("/destinations", response_model=List[schemas.DestinationResponse])
async def get_all_destinations(
    region: str = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get destinations, optionally filtered by region"""
    if region:
        destinations = crud.get_destinations_by_region(db, region=region, limit=limit)
    else:
        destinations = crud.get_popular_destinations(db, limit=limit)
    
    return destinations

@router.get("/stats/public")
async def get_public_statistics(
    db: Session = Depends(get_db)
):
    """Get public statistics (no auth required)"""
    stats = crud.get_system_stats(db)
    popular = crud.get_popular_destinations_from_plans(db, limit=5)
    
    return {
        "total_plans_generated": stats['total_plans'],
        "active_users": stats['active_users_30d'],
        "top_destinations": [dest for dest, count in popular],
        "average_trip_duration": round(crud.get_average_plan_duration(db), 1)
    }