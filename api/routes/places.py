from fastapi import APIRouter, Depends, HTTPException
from langchain_community.utilities.tavily_search import TavilySearchAPIWrapper
import googlemaps
from typing import Optional, Dict, Any
from core.config import get_settings
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/places", tags=["places"])

def get_search_clients():
    """Get both Tavily and Google Places clients"""
    settings = get_settings()
    tavily_client = None
    gmaps_client = None
    
    try:
        tavily_client = TavilySearchAPIWrapper(tavily_api_key=settings.TAVILY_API_KEY)
    except Exception as e:
        logger.error(f"Tavily client initialization failed: {e}")
        
    try:
        gmaps_client = googlemaps.Client(key=settings.GOOGLE_API_KEY)
    except Exception as e:
        logger.error(f"Google Maps client initialization failed: {e}")
        
    if not tavily_client and not gmaps_client:
        raise HTTPException(
            status_code=500,
            detail="Failed to initialize search clients"
        )
    
    return {"tavily": tavily_client, "gmaps": gmaps_client}

@router.post("/search")
async def search_places(
    request: Dict[str, Any],
    clients: Dict[str, Any] = Depends(get_search_clients)
):
    place = request.get("place")
    search_type = request.get("search_type", "attractions")
    
    if not place:
        raise HTTPException(
            status_code=400,
            detail="Place parameter is required"
        )
    
    results = {}
    errors = {}
    
    # Try Google Places API
    if clients["gmaps"]:
        try:
            # First get place ID using places autocomplete
            autocomplete_result = clients["gmaps"].places_autocomplete(
                input_text=place,
                types=["(cities)"]
            )
            
            if autocomplete_result:
                place_id = autocomplete_result[0]["place_id"]
                # Get place details
                place_result = clients["gmaps"].place(
                    place_id=place_id,
                    fields=["name", "formatted_address", "geometry", "rating", 
                           "type", "photo", "editorial_summary"]
                )
                
                # Search for attractions nearby
                nearby_places = clients["gmaps"].places_nearby(
                    location=place_result["result"]["geometry"]["location"],
                    radius=5000,  # 5km radius
                    type=search_type
                )
                
                results["google"] = {
                    "place_info": place_result["result"],
                    "attractions": nearby_places["results"]
                }
        except Exception as e:
            logger.error(f"Google Places API error: {e}")
            errors["google"] = str(e)
    
    # Get additional information from Tavily
    if clients["tavily"]:
        try:
            query = f"Top tourist attractions and places to visit in {place}"
            tavily_results = clients["tavily"].run(query)
            results["tavily"] = tavily_results
        except Exception as e:
            logger.error(f"Tavily API error: {e}")
            errors["tavily"] = str(e)
    
    if not results:
        raise HTTPException(
            status_code=500,
            detail=f"Search failed. Errors: {json.dumps(errors)}"
        )
    
    response = {
        "place": place,
        "search_type": search_type,
        "results": results,
        "timestamp": str(datetime.now().isoformat())
    }
    
    if errors:
        response["errors"] = errors
        
    return response