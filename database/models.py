from sqlalchemy import (
    Column, Integer, String, Text, Float, Boolean, 
    DateTime, ForeignKey, JSON, Enum as SQLEnum
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database.base import Base
import enum

class UserRole(str, enum.Enum):
    """User role enumeration"""
    USER = "user"
    PREMIUM = "premium"
    ADMIN = "admin"

class PlanStatus(str, enum.Enum):
    """Travel plan status"""
    DRAFT = "draft"
    COMPLETED = "completed"
    ARCHIVED = "archived"

class User(Base):
    """User accounts table"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=False, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(SQLEnum(UserRole), default=UserRole.USER)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True))
    
    # Relationships
    travel_plans = relationship("TravelPlan", back_populates="user", cascade="all, delete-orphan")
    queries = relationship("Query", back_populates="user", cascade="all, delete-orphan")
    favorites = relationship("Favorite", back_populates="user", cascade="all, delete-orphan")
    api_usage = relationship("ApiUsage", back_populates="user", cascade="all, delete-orphan")

class TravelPlan(Base):
    """Travel plans/itineraries table"""
    __tablename__ = "travel_plans"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Basic info
    title = Column(String(255), nullable=False, index=True)  # Add index for search
    destination = Column(String(255), nullable=False, index=True)
    duration = Column(Integer, nullable=False)  # days
    budget = Column(Float)
    currency = Column(String(3), default="USD")
    
    # Content
    content = Column(Text, nullable=False)  # Full markdown content
    summary = Column(Text)  # Short summary
    
    # Metadata
    preferences = Column(JSON)  # ["cultural", "adventure"]
    group_size = Column(Integer, default=1)
    status = Column(SQLEnum(PlanStatus), default=PlanStatus.COMPLETED)
    
    # Additional data
    weather_data = Column(JSON)
    cost_breakdown = Column(JSON)
    attractions = Column(JSON)
    restaurants = Column(JSON)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)  # Add index for sorting
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="travel_plans")

class Query(Base):
    """User query history"""
    __tablename__ = "queries"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), index=True)
    
    query_text = Column(Text, nullable=False)
    response_length = Column(Integer)
    status_code = Column(Integer)
    execution_time = Column(Float)  # seconds
    
    # Request metadata
    ip_address = Column(String(45))
    user_agent = Column(String(255))
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Relationships
    user = relationship("User", back_populates="queries")

class Destination(Base):
    """Popular destinations reference table"""
    __tablename__ = "destinations"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    country = Column(String(100))
    region = Column(String(100))  # asia, europe, americas, etc.
    category = Column(String(100))  # beach, mountain, city, cultural
    
    description = Column(Text)
    best_time_to_visit = Column(String(100))
    average_budget = Column(Float)
    popularity_score = Column(Integer, default=0)
    
    # JSON data
    highlights = Column(JSON)
    weather_info = Column(JSON)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class Favorite(Base):
    """User favorite destinations"""
    __tablename__ = "favorites"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    destination_name = Column(String(255), nullable=False)
    notes = Column(Text)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="favorites")

class ApiUsage(Base):
    """API usage tracking"""
    __tablename__ = "api_usage"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    endpoint = Column(String(255), nullable=False, index=True)
    method = Column(String(10))  # GET, POST, etc.
    status_code = Column(Integer)
    response_time = Column(Float)  # milliseconds
    ip_address = Column(String(45))
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="api_usage")
