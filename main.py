# =============================================================================
# FILE: main.py - Updated with Database Integration
# =============================================================================
from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from contextlib import asynccontextmanager
import asyncio
import os
import datetime
import logging
import time
from typing import Optional, Dict, Any
from dotenv import load_dotenv

# Import existing modules
from agent.agentic_workflow import GraphBuilder
from utils.save_to_document import save_document

# Import API components
from api.models import (
    QueryRequest, 
    TravelPlanResponse, 
    HealthResponse,
    TravelPlanRequest,
    ErrorResponse
)
from api.dependencies import get_graph_builder, validate_api_key, check_rate_limit
from api.legacy_routes import weather_router, currency_router, places_router, analytics_router

# Import database
from database.base import engine, init_db, get_db
from database import models, crud, schemas
from sqlalchemy.orm import Session

# Import new database routes
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'api', 'routes'))
import plans_routes
import favorites_routes
import user_routes
import admin_routes
import public_routes

from core.config import get_settings, validate_environment
from core.logging_config import setup_logging

# Load environment variables
load_dotenv()

# Validate environment
validate_environment()

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Application lifespan manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown"""
    logger.info("🚀 Starting AI Travel Planner API with Database...")
    
    # Startup logic
    try:
        settings = get_settings()
        
        # Create necessary directories
        os.makedirs(settings.OUTPUT_DIR, exist_ok=True)
        os.makedirs(settings.GRAPHS_DIR, exist_ok=True)
        os.makedirs(settings.LOGS_DIR, exist_ok=True)
        
        # Initialize database
        try:
            logger.info("🗄️  Initializing database...")
            init_db()
            logger.info("✅ Database initialized successfully")
        except Exception as e:
            logger.error(f"❌ Database initialization failed: {e}")
            logger.warning("⚠️  Continuing without database (legacy mode)")
        
        # Test critical services
        try:
            graph_builder = get_graph_builder()
            logger.info("✅ AI Agent initialized successfully")
        except Exception as e:
            logger.warning(f"⚠️ AI Agent initialization warning: {e}")
        
        logger.info(f"✅ API started successfully on {settings.HOST}:{settings.PORT}")
        yield
        
    except Exception as e:
        logger.error(f"❌ Failed to start application: {e}")
        raise
    finally:
        # Cleanup logic
        logger.info("🔄 Shutting down AI Travel Planner API...")

# Create FastAPI app
app = FastAPI(
    title="🌍 AI Travel Planner API",
    description="""
    An intelligent travel planning API powered by AI agents with **PostgreSQL database** support.
    
    ## 🎯 New Features with Database:
    - **User Accounts** - Register and login
    - **Save Travel Plans** - Keep your itineraries forever
    - **Favorites** - Bookmark destinations
    - **History** - View your search history
    - **Dashboard** - Personal statistics and analytics
    
    ## 📋 Core Features:
    - 🎯 **Complete Travel Plans**: Comprehensive itineraries with day-by-day schedules
    - 🌤️ **Real-time Weather**: Current conditions and forecasts
    - 💰 **Cost Calculations**: Detailed budget breakdowns and currency conversion
    - 🏛️ **Place Discovery**: Attractions, restaurants, and activities
    - 🚌 **Transportation**: Local and inter-city travel options
    - 📊 **Analytics**: Usage statistics and popular destinations
    
    ## 🔐 Authentication:
    Most endpoints require authentication. To use them:
    1. Register: `POST /auth/register`
    2. Login: `POST /auth/token`
    3. Use the token in `Authorization: Bearer <token>` header
    
    ## 📚 Quick Start:
    1. **No Auth Required**: `/public/*`, `/health`, `/destinations`
    2. **With Auth**: `/plans/*`, `/favorites/*`, `/users/me/*`
    3. **Admin Only**: `/admin/*`
    """,
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    contact={
        "name": "AI Travel Planner Support",
        "email": "support@example.com",
    },
    license_info={
        "name": "MIT",
    }
)

# Add CORS middleware
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Include routers - Database routes (NEW)
# Note: auth_routes contains authentication functions, not a router
app.include_router(plans_routes.router)
app.include_router(favorites_routes.router)
app.include_router(user_routes.router)
app.include_router(admin_routes.router)
app.include_router(public_routes.router)

# Include routers - Existing API routes
app.include_router(weather_router)
app.include_router(currency_router)
app.include_router(places_router)
app.include_router(analytics_router)

# Middleware for API usage tracking
@app.middleware("http")
async def log_api_usage(request: Request, call_next):
    """Track API usage in database"""
    start_time = time.time()
    
    # Process request
    response = await call_next(request)
    
    # Calculate response time
    response_time = (time.time() - start_time) * 1000  # milliseconds
    
    # Log to database (in background)
    try:
        db = next(get_db())
        try:
            # Get user_id if authenticated
            user_id = None
            if hasattr(request.state, "user"):
                user_id = request.state.user.id
            
            # Log API usage
            crud.create_api_usage(
                db=db,
                endpoint=str(request.url.path),
                method=request.method,
                status_code=response.status_code,
                response_time=response_time,
                user_id=user_id,
                ip_address=request.client.host if request.client else None
            )
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Failed to log API usage: {e}")
    
    return response

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Global exception on {request.url}: {exc}")
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal server error",
            message="An unexpected error occurred. Please try again later.",
            timestamp=datetime.datetime.now().isoformat(),
            details={"url": str(request.url), "method": request.method}
        ).dict()
    )

# Root endpoints
@app.get("/", response_model=HealthResponse, tags=["Health"])
@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        message="🌍 Welcome to AI Trip Planner API v2.0 with Database! Use /docs to explore all features.",
        timestamp=datetime.datetime.now().isoformat(),
        version="2.0.0"
    )

# Legacy endpoints (kept for backward compatibility)
@app.post("/query", response_model=TravelPlanResponse, tags=["🎯 Legacy Travel Planning"])
async def query_travel_agent(
    query: QueryRequest,
    background_tasks: BackgroundTasks,
    _: bool = Depends(check_rate_limit),
    graph_builder: GraphBuilder = Depends(get_graph_builder),
    db: Session = Depends(get_db)
):
    """
    🎯 **Legacy endpoint - Generate travel plan (No authentication required)**
    
    **Note**: This endpoint doesn't save to database. Use `/plans/generate` with authentication to save plans.
    
    Simply describe your travel needs and get a complete plan including:
    - 📅 Day-by-day itinerary (tourist + offbeat routes)
    - 🏨 Hotel recommendations with pricing
    - 🎯 Top attractions and activities
    - 🍽️ Restaurant suggestions
    - 🚌 Transportation options
    - 💰 Detailed cost breakdown
    - 🌤️ Weather information
    - 💱 Currency conversion to INR
    
    **Examples:**
    - "Plan a 5-day trip to Paris with $2000 budget"
    - "Romantic getaway to Bali for 7 days"
    - "Adventure trip to New Zealand for 2 weeks"
    """
    try:
        start_time = time.time()
        logger.info(f"📝 Processing travel query: {query.question[:100]}...")
        
        # Build the agent graph
        react_app = graph_builder()
        
        # Save graph visualization in background
        background_tasks.add_task(save_graph_visualization, react_app)
        
        # Process the query
        messages = {"messages": [query.question]}
        output = react_app.invoke(messages)
        
        # Extract the response
        if isinstance(output, dict) and "messages" in output:
            final_output = output["messages"][-1].content
        else:
            final_output = str(output)
        
        execution_time = time.time() - start_time
        
        # Save document in background
        background_tasks.add_task(save_travel_plan, final_output, query.question)
        
        # Log query to database (anonymous)
        try:
            query_log = schemas.QueryCreate(
                query_text=query.question,
                response_length=len(final_output),
                status_code=200,
                execution_time=execution_time
            )
            crud.create_query(db=db, query=query_log, user_id=None)
        except Exception as e:
            logger.warning(f"Failed to log query to database: {e}")
        
        logger.info("✅ Travel plan generated successfully")
        
        return TravelPlanResponse(
            answer=final_output,
            status="success",
            timestamp=datetime.datetime.now().isoformat(),
            query=query.question
        )
        
    except Exception as e:
        logger.error(f"❌ Error processing query: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate travel plan: {str(e)}"
        )

@app.post("/plan-trip", response_model=TravelPlanResponse, tags=["🎯 Legacy Travel Planning"])
async def plan_detailed_trip(
    request: TravelPlanRequest,
    background_tasks: BackgroundTasks,
    _: bool = Depends(check_rate_limit),
    graph_builder: GraphBuilder = Depends(get_graph_builder)
):
    """
    🎯 **Legacy endpoint - Create detailed travel plan (No authentication required)**
    
    **Note**: This endpoint doesn't save to database. Use `/plans/generate` with authentication to save plans.
    """
    try:
        # Build comprehensive query from request parameters
        query_parts = [f"Plan a {request.duration}-day trip to {request.destination}"]
        
        if request.budget:
            query_parts.append(f"with a budget of {request.budget}")
        
        if request.preferences:
            query_parts.append(f"focusing on {', '.join(request.preferences)} activities")
        
        if request.group_size and request.group_size > 1:
            query_parts.append(f"for {request.group_size} people")
        
        if request.currency and request.currency != "USD":
            query_parts.append(f"with costs in {request.currency}")
        
        full_query = " ".join(query_parts)
        logger.info(f"🔧 Generated detailed query: {full_query}")
        
        # Use the existing query endpoint logic
        query_request = QueryRequest(question=full_query)
        return await query_travel_agent(query_request, background_tasks, True, graph_builder)
        
    except Exception as e:
        logger.error(f"❌ Error in detailed trip planning: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate detailed travel plan: {str(e)}"
        )

# Information endpoints
@app.get("/destinations", tags=["ℹ️ Information"])
async def get_popular_destinations():
    """🌍 **Get popular travel destinations by region and category**"""
    destinations = {
        "regions": {
            "asia": [
                {"name": "Tokyo, Japan", "type": "city", "highlights": ["technology", "culture", "food"], "best_time": "March-May, September-November"},
                {"name": "Bali, Indonesia", "type": "beach", "highlights": ["beaches", "temples", "nature"], "best_time": "April-October"},
                {"name": "Mumbai, India", "type": "city", "highlights": ["bollywood", "street food", "culture"], "best_time": "November-February"},
                {"name": "Bangkok, Thailand", "type": "city", "highlights": ["temples", "food", "nightlife"], "best_time": "November-March"},
                {"name": "Goa, India", "type": "beach", "highlights": ["beaches", "nightlife", "Portuguese heritage"], "best_time": "November-March"}
            ],
            "europe": [
                {"name": "Paris, France", "type": "city", "highlights": ["art", "culture", "romance"], "best_time": "April-June, September-November"},
                {"name": "Rome, Italy", "type": "city", "highlights": ["history", "art", "food"], "best_time": "April-June, September-October"},
                {"name": "Barcelona, Spain", "type": "city", "highlights": ["architecture", "beaches", "culture"], "best_time": "May-June, September-October"},
                {"name": "Amsterdam, Netherlands", "type": "city", "highlights": ["canals", "museums", "cycling"], "best_time": "April-May, September-November"}
            ],
            "americas": [
                {"name": "New York, USA", "type": "city", "highlights": ["skyline", "broadway", "museums"], "best_time": "April-June, September-November"},
                {"name": "Rio de Janeiro, Brazil", "type": "beach", "highlights": ["beaches", "carnival", "mountains"], "best_time": "December-March"},
                {"name": "Vancouver, Canada", "type": "city", "highlights": ["nature", "mountains", "ocean"], "best_time": "June-August"},
                {"name": "Mexico City, Mexico", "type": "city", "highlights": ["culture", "food", "history"], "best_time": "March-May, September-November"}
            ],
            "oceania": [
                {"name": "Sydney, Australia", "type": "city", "highlights": ["harbor", "beaches", "opera house"], "best_time": "September-November, March-May"},
                {"name": "Auckland, New Zealand", "type": "city", "highlights": ["nature", "adventure", "wine"], "best_time": "December-February, March-May"}
            ]
        },
        "categories": {
            "beach_destinations": ["Goa", "Bali", "Maldives", "Miami", "Santorini", "Phuket"],
            "mountain_destinations": ["Swiss Alps", "Himalayas", "Rocky Mountains", "Andes", "Nepal", "Patagonia"],
            "city_breaks": ["Paris", "Tokyo", "New York", "London", "Mumbai", "Barcelona"],
            "cultural_heritage": ["Rajasthan", "Egypt", "Greece", "Peru", "Morocco", "Jordan"],
            "adventure_destinations": ["New Zealand", "Costa Rica", "Iceland", "Nepal", "Patagonia", "Norway"],
            "romantic_getaways": ["Paris", "Santorini", "Bali", "Maldives", "Venice", "Kyoto"],
            "family_friendly": ["Dubai", "Singapore", "Orlando", "London", "Tokyo", "Gold Coast"],
            "budget_friendly": ["Vietnam", "India", "Guatemala", "Nepal", "Cambodia", "Bolivia"]
        },
        "trending_now": [
            {"destination": "Dubai, UAE", "reason": "Luxury shopping and experiences"},
            {"destination": "Iceland", "reason": "Northern lights and unique landscapes"},
            {"destination": "Portugal", "reason": "Affordable European destination"},
            {"destination": "South Korea", "reason": "K-culture and technology"},
            {"destination": "Colombia", "reason": "Emerging South American destination"}
        ]
    }
    return destinations

@app.get("/travel-tips", tags=["ℹ️ Information"])
async def get_travel_tips():
    """💡 **Get general travel tips and advice**"""
    return {
        "planning_tips": [
            "Book flights 6-8 weeks in advance for best prices",
            "Check visa requirements well in advance",
            "Get travel insurance for international trips",
            "Research local customs and etiquette",
            "Pack according to weather and cultural norms"
        ],
        "budget_tips": [
            "Use travel comparison websites for deals",
            "Consider staying in hostels or Airbnb",
            "Eat at local restaurants instead of touristy places",
            "Use public transportation when possible",
            "Look for free walking tours and attractions"
        ],
        "safety_tips": [
            "Register with your embassy for international travel",
            "Keep copies of important documents",
            "Share your itinerary with someone at home",
            "Research common scams in your destination",
            "Keep emergency contacts easily accessible"
        ],
        "packing_essentials": [
            "Universal power adapter",
            "Comfortable walking shoes",
            "First aid kit and medications",
            "Portable charger/power bank",
            "Travel documents organizer"
        ]
    }

# File management endpoints
@app.get("/download-plan/{filename}", tags=["📁 Files"])
async def download_travel_plan(filename: str):
    """📥 **Download a generated travel plan as a markdown file**"""
    file_path = os.path.join(settings.OUTPUT_DIR, filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        file_path,
        media_type="application/octet-stream",
        filename=filename
    )

@app.get("/list-plans", tags=["📁 Files"])
async def list_saved_plans():
    """📋 **List all saved travel plans (files)**"""
    try:
        output_dir = settings.OUTPUT_DIR
        if not os.path.exists(output_dir):
            return {"plans": []}
        
        files = []
        for filename in os.listdir(output_dir):
            if filename.endswith('.md'):
                file_path = os.path.join(output_dir, filename)
                stat = os.stat(file_path)
                files.append({
                    "filename": filename,
                    "created": datetime.datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    "size": stat.st_size,
                    "download_url": f"/download-plan/{filename}"
                })
        
        # Sort by creation date, newest first
        files.sort(key=lambda x: x["created"], reverse=True)
        
        return {"plans": files}
        
    except Exception as e:
        logger.error(f"Error listing plans: {e}")
        raise HTTPException(status_code=500, detail="Failed to list saved plans")

# API status and statistics
@app.get("/status", tags=["📊 System"])
async def get_api_status():
    """📊 **Get comprehensive API status and information**"""
    return {
        "status": "operational",
        "uptime": datetime.datetime.now().isoformat(),
        "version": "2.0.0",
        "database": "SQLite enabled",
        "environment": os.getenv("ENVIRONMENT", "development"),
        "features": {
            "ai_planning": "✅ AI-powered comprehensive travel planning",
            "user_accounts": "✅ User registration and authentication",
            "save_plans": "✅ Save and manage travel plans",
            "favorites": "✅ Bookmark favorite destinations",
            "history": "✅ Query and plan history tracking",
            "real_time_weather": "✅ Live weather data and forecasts",
            "cost_calculation": "✅ Detailed budget breakdowns",
            "currency_conversion": "✅ Multi-currency support",
            "place_discovery": "✅ Attractions, restaurants, activities",
            "transportation": "✅ Local and inter-city options",
            "document_export": "✅ Markdown file generation",
            "api_analytics": "✅ Usage statistics and monitoring",
            "admin_dashboard": "✅ Admin statistics and management"
        },
        "endpoints": {
            "authentication": ["/auth/register", "/auth/token", "/auth/me"],
            "travel_plans": ["/plans/generate", "/plans/", "/plans/{id}"],
            "favorites": ["/favorites/", "/favorites/{id}"],
            "user_dashboard": ["/users/me/stats", "/users/me/history"],
            "public": ["/public/popular-destinations", "/public/stats"],
            "legacy": ["/query", "/plan-trip"],
            "weather": ["/weather/current", "/weather/forecast"],
            "currency": ["/currency/convert", "/currency/rates"],
            "places": ["/places/search", "/places/popular"],
            "information": ["/destinations", "/travel-tips"],
            "files": ["/download-plan", "/list-plans"],
            "system": ["/health", "/status", "/analytics/stats"],
            "admin": ["/admin/stats", "/admin/users"]
        },
        "supported_destinations": "🌍 Worldwide coverage",
        "supported_currencies": "💱 150+ currencies supported",
        "data_sources": [
            "OpenWeatherMap API",
            "Google Places API", 
            "Tavily Search API",
            "Exchange Rate API",
            "AI Language Models (Groq/OpenAI)",
            "PostgreSQL Database"
        ]
    }

# Background tasks
async def save_graph_visualization(react_app):
    """Save the agent graph visualization"""
    try:
        png_graph = react_app.get_graph().draw_mermaid_png()
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"graph_{timestamp}.png"
        
        os.makedirs(settings.GRAPHS_DIR, exist_ok=True)
        with open(os.path.join(settings.GRAPHS_DIR, filename), "wb") as f:
            f.write(png_graph)
        
        logger.info(f"📊 Graph saved as {filename}")
    except Exception as e:
        logger.warning(f"⚠️ Could not save graph: {e}")

async def save_travel_plan(content: str, query: str = ""):
    """Save the travel plan to a markdown file"""
    try:
        filename = save_document(content)
        logger.info(f"💾 Travel plan saved: {filename}")
        
        # Log the query for analytics
        if query:
            logger.info(f"📝 Query processed: {query[:50]}...")
            
    except Exception as e:
        logger.warning(f"⚠️ Could not save travel plan: {e}")

# Development and testing endpoints (only in debug mode)
if settings.DEBUG:
    @app.get("/debug/test-tools", tags=["🔧 Debug"])
    async def test_all_tools():
        """🔧 **Test all AI tools (Debug mode only)**"""
        try:
            results = {}
            
            # Test weather tool
            try:
                from tools.weather_info_tool import WeatherInfoTool
                weather_tool = WeatherInfoTool()
                weather_result = weather_tool.weather_tool_list[0].invoke({"city": "London"})
                results["weather"] = "✅ Working"
            except Exception as e:
                results["weather"] = f"❌ Error: {str(e)}"
            
            # Test places tool
            try:
                from tools.place_search_tool import PlaceSearchTool
                places_tool = PlaceSearchTool()
                places_result = places_tool.place_search_tool_list[0].invoke({"place": "Paris"})
                results["places"] = "✅ Working"
            except Exception as e:
                results["places"] = f"❌ Error: {str(e)}"
            
            # Test currency tool
            try:
                from tools.currency_conversion_tool import CurrencyConverterTool
                currency_tool = CurrencyConverterTool()
                currency_result = currency_tool.currency_converter_tool_list[0].invoke({
                    "amount": 100.0, "from_currency": "USD", "to_currency": "EUR"
                })
                results["currency"] = "✅ Working"
            except Exception as e:
                results["currency"] = f"❌ Error: {str(e)}"
            
            # Test database
            try:
                db = next(get_db())
                stats = crud.get_system_stats(db)
                db.close()
                results["database"] = "✅ Working"
            except Exception as e:
                results["database"] = f"❌ Error: {str(e)}"
            
            return {
                "status": "debug_mode",
                "tool_tests": results,
                "timestamp": datetime.datetime.now().isoformat()
            }
            
        except Exception as e:
            return {"error": f"Debug test failed: {str(e)}"}
    
    @app.get("/debug/db-stats", tags=["🔧 Debug"])
    async def get_database_stats(db: Session = Depends(get_db)):
        """🔧 **Get database statistics (Debug mode only)**"""
        try:
            stats = crud.get_system_stats(db)
            
            return {
                "database": "connected",
                "statistics": stats,
                "tables": {
                    "users": db.query(models.User).count(),
                    "travel_plans": db.query(models.TravelPlan).count(),
                    "queries": db.query(models.Query).count(),
                    "favorites": db.query(models.Favorite).count(),
                    "destinations": db.query(models.Destination).count(),
                    "api_usage": db.query(models.ApiUsage).count()
                },
                "timestamp": datetime.datetime.now().isoformat()
            }
        except Exception as e:
            return {"error": f"Database stats failed: {str(e)}"}

# Run the application
if __name__ == "__main__":
    import uvicorn
    
    # Load settings
    settings = get_settings()
    
    # Run with appropriate configuration
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info" if not settings.DEBUG else "debug",
        access_log=True
    )