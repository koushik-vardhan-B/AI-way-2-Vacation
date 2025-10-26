from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import List, Dict, Any
import datetime
import logging

from agent.agentic_workflow import GraphBuilder
from api.models import (
    WeatherRequest, WeatherResponse,
    CurrencyConversionRequest, CurrencyConversionResponse,
    PlaceSearchRequest, PlaceSearchResponse,
    TripSummary, ApiStats
)
from api.dependencies import get_graph_builder, validate_api_key, check_rate_limit
from tools.weather_info_tool import WeatherInfoTool
from tools.currency_conversion_tool import CurrencyConverterTool
from tools.place_search_tool import PlaceSearchTool

logger = logging.getLogger(__name__)

# Create router instances
weather_router = APIRouter(prefix="/weather", tags=["Weather"])
currency_router = APIRouter(prefix="/currency", tags=["Currency"])
places_router = APIRouter(prefix="/places", tags=["Places"])
analytics_router = APIRouter(prefix="/analytics", tags=["Analytics"])


# Currency endpoints

@currency_router.post("/convert", response_model=CurrencyConversionResponse)
async def convert_currency(
    request: CurrencyConversionRequest
    # REMOVE: _: bool = Depends(validate_api_key),
    # REMOVE: __: bool = Depends(check_rate_limit)
):
    """Convert amount from one currency to another"""
    try:
        currency_tool = CurrencyConverterTool()
        convert_tool = currency_tool.currency_converter_tool_list[0]
        
        result = convert_tool.invoke({
            "amount": request.amount,
            "from_currency": request.from_currency,
            "to_currency": request.to_currency
        })
        
        # Calculate exchange rate
        exchange_rate = result / request.amount if request.amount > 0 else 0
        
        return CurrencyConversionResponse(
            original_amount=request.amount,
            converted_amount=result,
            from_currency=request.from_currency,
            to_currency=request.to_currency,
            exchange_rate=exchange_rate,
            timestamp=datetime.datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error converting currency: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to convert currency: {str(e)}"
        )

@weather_router.post("/current", response_model=WeatherResponse)
async def get_current_weather(
    request: WeatherRequest
    # REMOVE: _: bool = Depends(validate_api_key),
    # REMOVE: __: bool = Depends(check_rate_limit)
):
    """Get current weather for a specific city"""
    try:
        weather_tool = WeatherInfoTool()
        
        # Get current weather
        current_weather_tool = weather_tool.weather_tool_list[0]  # get_current_weather
        current_result = current_weather_tool.invoke({"city": request.city})
        
        # Get forecast
        forecast_tool = weather_tool.weather_tool_list[1]  # get_weather_forecast
        forecast_result = forecast_tool.invoke({"city": request.city})
        
        return WeatherResponse(
            city=request.city,
            current_weather={"description": current_result},
            forecast=[{"description": forecast_result}],
            timestamp=datetime.datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error fetching weather for {request.city}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch weather data: {str(e)}"
        )

@weather_router.get("/forecast/{city}")
async def get_weather_forecast(
    city: str
    # REMOVE: _: bool = Depends(validate_api_key)
):
    """Get weather forecast for a city"""
    try:
        weather_tool = WeatherInfoTool()
        forecast_tool = weather_tool.weather_tool_list[1]
        result = forecast_tool.invoke({"city": city})
        
        return {
            "city": city,
            "forecast": result,
            "timestamp": datetime.datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error fetching forecast for {city}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Also fix the currency rates endpoint if it exists
@currency_router.get("/rates/{base_currency}")
async def get_exchange_rates(
    base_currency: str
    # REMOVE: _: bool = Depends(validate_api_key)
):
    """Get current exchange rates for a base currency"""
    try:
        # Common currencies to show rates for
        target_currencies = ["USD", "EUR", "GBP", "JPY", "INR", "CAD", "AUD"]
        
        currency_tool = CurrencyConverterTool()
        convert_tool = currency_tool.currency_converter_tool_list[0]
        
        rates = {}
        for target in target_currencies:
            if target != base_currency.upper():
                try:
                    result = convert_tool.invoke({
                        "amount": 1.0,
                        "from_currency": base_currency.upper(),
                        "to_currency": target
                    })
                    rates[target] = result
                except Exception as e:
                    logger.warning(f"Failed to get rate for {target}: {e}")
                    rates[target] = None
        
        return {
            "base_currency": base_currency.upper(),
            "rates": rates,
            "timestamp": datetime.datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error fetching exchange rates: {e}")
        raise HTTPException(status_code=500, detail=str(e))
# Places endpoints
@places_router.post("/search", response_model=PlaceSearchResponse)
async def search_places(
    request: PlaceSearchRequest,
    _: bool = Depends(validate_api_key),
    __: bool = Depends(check_rate_limit)
):
    """Search for places based on type (attractions, restaurants, activities, transportation)"""
    try:
        place_tool = PlaceSearchTool()
        
        # Map search type to appropriate tool
        tool_mapping = {
            "attractions": 0,
            "restaurants": 1,
            "activities": 2,
            "transportation": 3
        }
        
        tool_index = tool_mapping.get(request.search_type)
        if tool_index is None:
            raise ValueError(f"Invalid search type: {request.search_type}")
        
        search_tool = place_tool.place_search_tool_list[tool_index]
        result = search_tool.invoke({"place": request.place})
        
        return PlaceSearchResponse(
            place=request.place,
            search_type=request.search_type,
            results=result,
            timestamp=datetime.datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error searching places: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to search places: {str(e)}"
        )

@places_router.get("/popular")
async def get_popular_places():
    """Get popular travel destinations by category"""
    return {
        "destinations": {
            "asia": [
                {"name": "Tokyo, Japan", "type": "city", "highlights": ["technology", "culture", "food"]},
                {"name": "Bali, Indonesia", "type": "beach", "highlights": ["beaches", "temples", "nature"]},
                {"name": "Mumbai, India", "type": "city", "highlights": ["bollywood", "street food", "culture"]},
                {"name": "Bangkok, Thailand", "type": "city", "highlights": ["temples", "food", "nightlife"]}
            ],
            "europe": [
                {"name": "Paris, France", "type": "city", "highlights": ["art", "culture", "romance"]},
                {"name": "Rome, Italy", "type": "city", "highlights": ["history", "art", "food"]},
                {"name": "Barcelona, Spain", "type": "city", "highlights": ["architecture", "beaches", "culture"]},
                {"name": "Amsterdam, Netherlands", "type": "city", "highlights": ["canals", "museums", "cycling"]}
            ],
            "americas": [
                {"name": "New York, USA", "type": "city", "highlights": ["skyline", "broadway", "museums"]},
                {"name": "Rio de Janeiro, Brazil", "type": "beach", "highlights": ["beaches", "carnival", "mountains"]},
                {"name": "Vancouver, Canada", "type": "city", "highlights": ["nature", "mountains", "ocean"]},
                {"name": "Buenos Aires, Argentina", "type": "city", "highlights": ["tango", "culture", "food"]}
            ]
        },
        "categories": {
            "beach": ["Bali", "Goa", "Maldives", "Miami", "Santorini"],
            "mountains": ["Swiss Alps", "Himalayas", "Rocky Mountains", "Andes"],
            "cities": ["Paris", "Tokyo", "New York", "London"],
            "cultural": ["Rajasthan", "Egypt", "Greece", "Peru"],
            "adventure": ["New Zealand", "Costa Rica", "Iceland", "Nepal"]
        }
    }

# Analytics endpoints
@analytics_router.get("/stats", response_model=ApiStats)
async def get_api_statistics():
    """Get API usage statistics"""
    # In a real application, these would come from a database
    return ApiStats(
        total_queries=1250,
        successful_plans=1180,
        error_rate=5.6,
        uptime=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        popular_destinations=["Paris", "Tokyo", "New York", "Bali", "London"]
    )

@analytics_router.get("/health-detailed")
async def get_detailed_health():
    """Get detailed health information about all services"""
    try:
        # Test all critical services
        health_status = {
            "api": "healthy",
            "ai_agent": "unknown",
            "weather_service": "unknown",
            "places_service": "unknown",
            "currency_service": "unknown"
        }
        
        # Test AI agent
        try:
            graph_builder = get_graph_builder()
            health_status["ai_agent"] = "healthy"
        except Exception as e:
            health_status["ai_agent"] = f"unhealthy: {str(e)}"
        
        # Test weather service
        try:
            weather_tool = WeatherInfoTool()
            health_status["weather_service"] = "healthy"
        except Exception as e:
            health_status["weather_service"] = f"unhealthy: {str(e)}"
        
        # Test places service
        try:
            place_tool = PlaceSearchTool()
            health_status["places_service"] = "healthy"
        except Exception as e:
            health_status["places_service"] = f"unhealthy: {str(e)}"
        
        # Test currency service
        try:
            currency_tool = CurrencyConverterTool()
            health_status["currency_service"] = "healthy"
        except Exception as e:
            health_status["currency_service"] = f"unhealthy: {str(e)}"
        
        overall_health = "healthy" if all(
            status == "healthy" for status in health_status.values()
        ) else "degraded"
        
        return {
            "overall_status": overall_health,
            "services": health_status,
            "timestamp": datetime.datetime.now().isoformat(),
            "uptime": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
    except Exception as e:
        logger.error(f"Error in health check: {e}")
        return {
            "overall_status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.datetime.now().isoformat()
        }