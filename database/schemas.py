from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

# Enums
class UserRole(str, Enum):
    USER = "user"
    PREMIUM = "premium"
    ADMIN = "admin"

class PlanStatus(str, Enum):
    DRAFT = "draft"
    COMPLETED = "completed"
    ARCHIVED = "archived"

# ===== User Schemas =====
class UserBase(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)

class UserCreate(UserBase):
    username: str
    email: str  # Try with str instead of EmailStr first
    password: str

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=8)

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    
    class Config:
        from_attributes = True

# In your schemas.py

class UserLogin(BaseModel):
    email: str
    password: str

class TokenWithUser(BaseModel):
    access_token: str
    token_type: str
    username: str
    email: str
    
    class Config:
        from_attributes = True

class GoogleAuth(BaseModel):
    email: str
    username: str

class ForgotPasswordRequest(BaseModel):
    email: str

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=6)

# ===== Travel Plan Schemas =====
class TravelPlanBase(BaseModel):
    title: str = Field(..., min_length=5, max_length=255)
    destination: str = Field(..., min_length=2, max_length=255)
    duration: int = Field(..., ge=1, le=90)
    budget: Optional[float] = Field(None, ge=0)
    currency: str = Field("USD", min_length=3, max_length=3)
    preferences: Optional[List[str]] = None
    group_size: int = Field(1, ge=1, le=20)

class TravelPlanCreate(TravelPlanBase):
    content: str
    summary: Optional[str] = None
    weather_data: Optional[Dict[str, Any]] = None
    cost_breakdown: Optional[Dict[str, Any]] = None
    attractions: Optional[List[str]] = None
    restaurants: Optional[List[str]] = None

class TravelPlanUpdate(BaseModel):
    title: Optional[str] = None
    status: Optional[PlanStatus] = None
    content: Optional[str] = None
    summary: Optional[str] = None

class TravelPlanResponse(TravelPlanBase):
    id: int
    user_id: int
    content: str
    summary: Optional[str]
    status: PlanStatus
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class TravelPlanListResponse(BaseModel):
    """Lightweight response for listing plans"""
    id: int
    title: str
    destination: str
    duration: int
    budget: Optional[float]
    status: PlanStatus
    created_at: datetime
    
    class Config:
        from_attributes = True


# ===== Query Schemas =====
class QueryCreate(BaseModel):
    query_text: str
    response_length: Optional[int] = None
    status_code: Optional[int] = None
    execution_time: Optional[float] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

class QueryResponse(BaseModel):
    id: int
    query_text: str
    created_at: datetime
    execution_time: Optional[float]
    
    class Config:
        from_attributes = True

# ===== Favorite Schemas =====
class FavoriteCreate(BaseModel):
    destination_name: str = Field(..., min_length=2, max_length=255)
    notes: Optional[str] = None

class FavoriteResponse(FavoriteCreate):
    id: int
    user_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# ===== Destination Schemas =====
class DestinationResponse(BaseModel):
    id: int
    name: str
    country: Optional[str]
    region: Optional[str]
    category: Optional[str]
    popularity_score: int
    
    class Config:
        from_attributes = True

# ===== Auth Schemas =====
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    username: Optional[str] = None

class LoginRequest(BaseModel):
    username: str
    password: str

# ===== Statistics Schemas =====
class UserStatsResponse(BaseModel):
    total_plans: int
    total_queries: int
    favorite_destinations: int
    member_since: datetime

class PopularDestinationResponse(BaseModel):
    destination: str
    count: int

