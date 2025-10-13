from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime

class QueryRequest(BaseModel):
    """Request model for basic travel query"""
    question: str = Field(
        ..., 
        description="Travel planning question",
        min_length=5,
        max_length=1000,
        example="Plan a 5-day trip to Paris with a budget of $2000"
    )

class TravelPlanRequest(BaseModel):
    """Request model for detailed travel planning"""
    destination: str = Field(
        ..., 
        description="Travel destination",
        min_length=2,
        max_length=100,
        example="Paris, France"
    )
    duration: int = Field(
        ..., 
        description="Number of days for the trip",
        ge=1,
        le=30,
        example=5
    )
    budget: Optional[str] = Field(
        None,
        description="Budget for the trip",
        example="$2000"
    )
    preferences: Optional[List[str]] = Field(
        None,
        description="Travel preferences",
        example=["cultural", "adventure", "food"]
    )
    group_size: Optional[int] = Field(
        1,
        description="Number of travelers",
        ge=1,
        le=20,
        example=2
    )
    currency: Optional[str] = Field(
        "INR",
        description="Preferred currency for cost calculations",
        example="INR"
    )
    
    @validator('preferences')
    def validate_preferences(cls, v):
        if v is not None:
            valid_preferences = [
                'cultural', 'adventure', 'relaxing', 'food', 'nightlife',
                'shopping', 'nature', 'historical', 'beach', 'mountain',
                'city', 'luxury', 'budget', 'family', 'romantic'
            ]
            for pref in v:
                if pref.lower() not in valid_preferences:
                    raise ValueError(f"Invalid preference: {pref}. Valid options: {valid_preferences}")
        return v

class TravelPlanResponse(BaseModel):
    """Response model for travel planning"""
    answer: str = Field(..., description="Generated travel plan")
    status: str = Field(..., description="Response status")
    timestamp: str = Field(..., description="Response timestamp")
    query: str = Field(..., description="Original query")
    
class HealthResponse(BaseModel):
    """Response model for health check"""
    status: str = Field(..., description="Health status")
    message: str = Field(..., description="Health message")
    timestamp: str = Field(..., description="Response timestamp")
    version: str = Field(..., description="API version")

class ErrorResponse(BaseModel):
    """Response model for errors"""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    timestamp: str = Field(..., description="Error timestamp")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")

class WeatherRequest(BaseModel):
    """Request model for weather information"""
    city: str = Field(
        ..., 
        description="City name for weather information",
        min_length=2,
        max_length=100,
        example="Paris"
    )

class WeatherResponse(BaseModel):
    """Response model for weather information"""
    city: str = Field(..., description="City name")
    current_weather: Dict[str, Any] = Field(..., description="Current weather data")
    forecast: List[Dict[str, Any]] = Field(..., description="Weather forecast")
    timestamp: str = Field(..., description="Response timestamp")

class CurrencyConversionRequest(BaseModel):
    """Request model for currency conversion"""
    amount: float = Field(..., description="Amount to convert", gt=0)
    from_currency: str = Field(
        ..., 
        description="Source currency code",
        min_length=3,
        max_length=3,
        example="INR"
    )
    to_currency: str = Field(
        ..., 
        description="Target currency code",
        min_length=3,
        max_length=3,
        example="USD"
    )

class CurrencyConversionResponse(BaseModel):
    """Response model for currency conversion"""
    original_amount: float = Field(..., description="Original amount")
    converted_amount: float = Field(..., description="Converted amount")
    from_currency: str = Field(..., description="Source currency")
    to_currency: str = Field(..., description="Target currency")
    exchange_rate: float = Field(..., description="Exchange rate used")
    timestamp: str = Field(..., description="Conversion timestamp")

class PlaceSearchRequest(BaseModel):
    """Request model for place search"""
    place: str = Field(
        ..., 
        description="Place to search for",
        min_length=2,
        max_length=100,
        example="Paris"
    )
    search_type: str = Field(
        ..., 
        description="Type of search",
        example="attractions"
    )
    
    @validator('search_type')
    def validate_search_type(cls, v):
        valid_types = ['attractions', 'restaurants', 'activities', 'transportation']
        if v.lower() not in valid_types:
            raise ValueError(f"Invalid search type: {v}. Valid options: {valid_types}")
        return v.lower()

class PlaceSearchResponse(BaseModel):
    """Response model for place search"""
    place: str = Field(..., description="Searched place")
    search_type: str = Field(..., description="Type of search performed")
    results: str = Field(..., description="Search results")
    timestamp: str = Field(..., description="Search timestamp")

class TripSummary(BaseModel):
    """Model for trip summary"""
    destination: str
    duration: int
    total_cost: Optional[float] = None
    currency: str = "INR"
    created_at: str
    highlights: List[str] = []

class ApiStats(BaseModel):
    """Model for API statistics"""
    total_queries: int = 0
    successful_plans: int = 0
    error_rate: float = 0.0
    uptime: str
    popular_destinations: List[str] = []