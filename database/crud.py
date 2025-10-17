# =============================================================================
# FILE: database/crud.py - Complete CRUD Operations
# =============================================================================
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from typing import Optional, List
from datetime import datetime, timedelta
from database import models, schemas
from passlib.context import CryptContext

# Password hashing
# Use pbkdf2_sha256 to remove bcrypt's 72-byte input limitation entirely
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

# ===== User CRUD =====
def get_user(db: Session, user_id: int) -> Optional[models.User]:
    """Get user by ID"""
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_email(db: Session, email: str) -> Optional[models.User]:
    """Get user by email"""
    return db.query(models.User).filter(models.User.email == email).first()

def get_user_by_username(db: Session, username: str) -> Optional[models.User]:
    """Get user by username"""
    return db.query(models.User).filter(models.User.username == username).first()

def create_user(db: Session, user: schemas.UserCreate) -> models.User:
    """Create new user"""
    hashed_password = pwd_context.hash(user.password)
    db_user = models.User(
        email=user.email,
        username=user.username,
        full_name=user.full_name,
        hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password"""
    return pwd_context.verify(plain_password, hashed_password)

def update_last_login(db: Session, user_id: int):
    """Update user's last login timestamp"""
    user = get_user(db, user_id)
    if user:
        user.last_login = datetime.utcnow()
        db.commit()

def update_user(db: Session, user_id: int, user_update: schemas.UserUpdate) -> Optional[models.User]:
    """Update user information"""
    db_user = get_user(db, user_id)
    if db_user:
        update_data = user_update.dict(exclude_unset=True)
        
        # Hash password if being updated
        if 'password' in update_data:
            update_data['hashed_password'] = pwd_context.hash(update_data.pop('password'))
        
        for key, value in update_data.items():
            setattr(db_user, key, value)
        
        db.commit()
        db.refresh(db_user)
    return db_user

# ===== Travel Plan CRUD =====
def create_travel_plan(
    db: Session, 
    plan: schemas.TravelPlanCreate, 
    user_id: int
) -> models.TravelPlan:
    """Create new travel plan"""
    db_plan = models.TravelPlan(
        **plan.dict(),
        user_id=user_id
    )
    db.add(db_plan)
    db.commit()
    db.refresh(db_plan)
    return db_plan

def get_travel_plans(
    db: Session, 
    user_id: int, 
    skip: int = 0, 
    limit: int = 10
) -> List[models.TravelPlan]:
    """Get user's travel plans"""
    return db.query(models.TravelPlan)\
        .filter(models.TravelPlan.user_id == user_id)\
        .order_by(desc(models.TravelPlan.created_at))\
        .offset(skip)\
        .limit(limit)\
        .all()

def get_travel_plan(
    db: Session, 
    plan_id: int, 
    user_id: int
) -> Optional[models.TravelPlan]:
    """Get specific travel plan"""
    return db.query(models.TravelPlan)\
        .filter(
            models.TravelPlan.id == plan_id,
            models.TravelPlan.user_id == user_id
        )\
        .first()

def update_travel_plan(
    db: Session, 
    plan_id: int, 
    user_id: int, 
    plan_update: schemas.TravelPlanUpdate
) -> Optional[models.TravelPlan]:
    """Update travel plan"""
    db_plan = get_travel_plan(db, plan_id, user_id)
    if db_plan:
        for key, value in plan_update.dict(exclude_unset=True).items():
            setattr(db_plan, key, value)
        db.commit()
        db.refresh(db_plan)
    return db_plan

def delete_travel_plan(db: Session, plan_id: int, user_id: int) -> bool:
    """Delete travel plan"""
    db_plan = get_travel_plan(db, plan_id, user_id)
    if db_plan:
        db.delete(db_plan)
        db.commit()
        return True
    return False

def get_all_travel_plans_by_destination(
    db: Session,
    destination: str,
    limit: int = 10
) -> List[models.TravelPlan]:
    """Get all plans for a destination (for admin/analytics)"""
    return db.query(models.TravelPlan)\
        .filter(models.TravelPlan.destination.ilike(f"%{destination}%"))\
        .order_by(desc(models.TravelPlan.created_at))\
        .limit(limit)\
        .all()

# ===== Query CRUD =====
def create_query(
    db: Session, 
    query: schemas.QueryCreate, 
    user_id: Optional[int] = None
) -> models.Query:
    """Create query record"""
    db_query = models.Query(
        **query.dict(),
        user_id=user_id
    )
    db.add(db_query)
    db.commit()
    db.refresh(db_query)
    return db_query

def get_user_queries(
    db: Session, 
    user_id: int, 
    limit: int = 20
) -> List[models.Query]:
    """Get user's query history"""
    return db.query(models.Query)\
        .filter(models.Query.user_id == user_id)\
        .order_by(desc(models.Query.created_at))\
        .limit(limit)\
        .all()

def get_recent_queries(db: Session, limit: int = 50) -> List[models.Query]:
    """Get recent queries (for admin)"""
    return db.query(models.Query)\
        .order_by(desc(models.Query.created_at))\
        .limit(limit)\
        .all()

# ===== Favorite CRUD =====
def create_favorite(
    db: Session, 
    favorite: schemas.FavoriteCreate, 
    user_id: int
) -> models.Favorite:
    """Create favorite destination"""
    # Check if already exists
    existing = db.query(models.Favorite)\
        .filter(
            models.Favorite.user_id == user_id,
            models.Favorite.destination_name == favorite.destination_name
        )\
        .first()
    
    if existing:
        return existing
    
    db_favorite = models.Favorite(
        **favorite.dict(),
        user_id=user_id
    )
    db.add(db_favorite)
    db.commit()
    db.refresh(db_favorite)
    return db_favorite

def get_user_favorites(db: Session, user_id: int) -> List[models.Favorite]:
    """Get user's favorite destinations"""
    return db.query(models.Favorite)\
        .filter(models.Favorite.user_id == user_id)\
        .order_by(desc(models.Favorite.created_at))\
        .all()

def delete_favorite(db: Session, favorite_id: int, user_id: int) -> bool:
    """Delete favorite destination"""
    db_favorite = db.query(models.Favorite)\
        .filter(
            models.Favorite.id == favorite_id,
            models.Favorite.user_id == user_id
        )\
        .first()
    
    if db_favorite:
        db.delete(db_favorite)
        db.commit()
        return True
    return False

def delete_favorite_by_name(
    db: Session, 
    destination_name: str, 
    user_id: int
) -> bool:
    """Delete favorite by destination name"""
    db_favorite = db.query(models.Favorite)\
        .filter(
            models.Favorite.destination_name == destination_name,
            models.Favorite.user_id == user_id
        )\
        .first()
    
    if db_favorite:
        db.delete(db_favorite)
        db.commit()
        return True
    return False

# ===== Destination CRUD =====
def get_or_create_destination(
    db: Session,
    name: str,
    country: Optional[str] = None,
    region: Optional[str] = None
) -> models.Destination:
    """Get existing destination or create new one"""
    destination = db.query(models.Destination)\
        .filter(models.Destination.name == name)\
        .first()
    
    if not destination:
        destination = models.Destination(
            name=name,
            country=country,
            region=region,
            popularity_score=1
        )
        db.add(destination)
        db.commit()
        db.refresh(destination)
    else:
        # Increment popularity
        destination.popularity_score += 1
        db.commit()
    
    return destination

def get_popular_destinations(db: Session, limit: int = 10) -> List[models.Destination]:
    """Get most popular destinations"""
    return db.query(models.Destination)\
        .order_by(desc(models.Destination.popularity_score))\
        .limit(limit)\
        .all()

def get_destinations_by_region(
    db: Session, 
    region: str, 
    limit: int = 20
) -> List[models.Destination]:
    """Get destinations by region"""
    return db.query(models.Destination)\
        .filter(models.Destination.region == region)\
        .order_by(desc(models.Destination.popularity_score))\
        .limit(limit)\
        .all()

# ===== API Usage CRUD =====
def create_api_usage(
    db: Session,
    endpoint: str,
    method: str,
    status_code: int,
    response_time: float,
    user_id: Optional[int] = None,
    ip_address: Optional[str] = None
) -> models.ApiUsage:
    """Record API usage"""
    db_usage = models.ApiUsage(
        user_id=user_id,
        endpoint=endpoint,
        method=method,
        status_code=status_code,
        response_time=response_time,
        ip_address=ip_address
    )
    db.add(db_usage)
    db.commit()
    db.refresh(db_usage)
    return db_usage

def get_user_api_usage(
    db: Session,
    user_id: int,
    days: int = 7
) -> List[models.ApiUsage]:
    """Get user's API usage for last N days"""
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    return db.query(models.ApiUsage)\
        .filter(
            models.ApiUsage.user_id == user_id,
            models.ApiUsage.created_at >= cutoff_date
        )\
        .order_by(desc(models.ApiUsage.created_at))\
        .all()

def get_endpoint_stats(db: Session, days: int = 7):
    """Get endpoint usage statistics"""
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    return db.query(
        models.ApiUsage.endpoint,
        func.count(models.ApiUsage.id).label('count'),
        func.avg(models.ApiUsage.response_time).label('avg_response_time')
    )\
        .filter(models.ApiUsage.created_at >= cutoff_date)\
        .group_by(models.ApiUsage.endpoint)\
        .order_by(desc('count'))\
        .all()

# ===== Analytics CRUD =====
def get_popular_destinations_from_plans(db: Session, limit: int = 10):
    """Get popular destinations from travel plans"""
    return db.query(
        models.TravelPlan.destination,
        func.count(models.TravelPlan.id).label('count')
    )\
        .group_by(models.TravelPlan.destination)\
        .order_by(desc('count'))\
        .limit(limit)\
        .all()

def get_user_stats(db: Session, user_id: int) -> dict:
    """Get comprehensive user statistics"""
    # Count plans
    total_plans = db.query(func.count(models.TravelPlan.id))\
        .filter(models.TravelPlan.user_id == user_id)\
        .scalar()
    
    # Count queries
    total_queries = db.query(func.count(models.Query.id))\
        .filter(models.Query.user_id == user_id)\
        .scalar()
    
    # Count favorites
    total_favorites = db.query(func.count(models.Favorite.id))\
        .filter(models.Favorite.user_id == user_id)\
        .scalar()
    
    # Get user
    user = get_user(db, user_id)
    
    return {
        "total_plans": total_plans or 0,
        "total_queries": total_queries or 0,
        "total_favorites": total_favorites or 0,
        "member_since": user.created_at if user else None,
        "last_login": user.last_login if user else None
    }

def get_system_stats(db: Session) -> dict:
    """Get overall system statistics"""
    total_users = db.query(func.count(models.User.id)).scalar()
    total_plans = db.query(func.count(models.TravelPlan.id)).scalar()
    total_queries = db.query(func.count(models.Query.id)).scalar()
    
    # Active users (logged in last 30 days)
    cutoff = datetime.utcnow() - timedelta(days=30)
    active_users = db.query(func.count(models.User.id))\
        .filter(models.User.last_login >= cutoff)\
        .scalar()
    
    # Plans created in last 7 days
    week_ago = datetime.utcnow() - timedelta(days=7)
    recent_plans = db.query(func.count(models.TravelPlan.id))\
        .filter(models.TravelPlan.created_at >= week_ago)\
        .scalar()
    
    return {
        "total_users": total_users or 0,
        "total_plans": total_plans or 0,
        "total_queries": total_queries or 0,
        "active_users_30d": active_users or 0,
        "plans_last_7d": recent_plans or 0
    }

def get_average_plan_duration(db: Session) -> float:
    """Get average trip duration"""
    avg_duration = db.query(func.avg(models.TravelPlan.duration)).scalar()
    return avg_duration or 0.0

def get_average_budget(db: Session) -> float:
    """Get average trip budget"""
    avg_budget = db.query(func.avg(models.TravelPlan.budget))\
        .filter(models.TravelPlan.budget.isnot(None))\
        .scalar()
    return avg_budget or 0.0

def search_travel_plans(
    db: Session,
    user_id: int,
    search_term: str,
    limit: int = 10
) -> List[models.TravelPlan]:
    """Search user's travel plans by destination or title"""
    search_pattern = f"%{search_term}%"
    return db.query(models.TravelPlan)\
        .filter(
            models.TravelPlan.user_id == user_id,
            (models.TravelPlan.destination.ilike(search_pattern) |
             models.TravelPlan.title.ilike(search_pattern))
        )\
        .order_by(desc(models.TravelPlan.created_at))\
        .limit(limit)\
        .all()
