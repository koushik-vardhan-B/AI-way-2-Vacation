from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, Optional
import googlemaps
from datetime import datetime
import logging
from pydantic import BaseModel

from api.auth import get_current_active_user
from database import schemas
from core.config import get_settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/directions", tags=["🧭 Directions"])


class DirectionsRequest(BaseModel):
    """Request for directions between two places"""
    origin: str
    destination: str
    mode: Optional[str] = "driving"  # driving, walking, bicycling, transit
    departure_time: Optional[str] = None  # ISO format datetime
    arrival_time: Optional[str] = None  # ISO format datetime
    alternatives: Optional[bool] = False
    avoid: Optional[str] = None  # tolls, highways, ferries


def get_gmaps_client():
    """Get Google Maps client"""
    settings = get_settings()
    try:
        return googlemaps.Client(key=settings.GOOGLE_API_KEY)
    except Exception as e:
        logger.error(f"Failed to initialize Google Maps client: {e}")
        raise HTTPException(
            status_code=500,
            detail="Google Maps service unavailable"
        )


@router.post("/get-directions")
async def get_directions(
    request: DirectionsRequest,
    current_user: schemas.UserResponse = Depends(get_current_active_user),
    gmaps: googlemaps.Client = Depends(get_gmaps_client)
):
    """
    Get directions between two locations
    
    Supports multiple travel modes:
    - driving (default)
    - walking
    - bicycling
    - transit (public transportation)
    
    Example request:
    {
        "origin": "Eiffel Tower, Paris",
        "destination": "Louvre Museum, Paris",
        "mode": "walking"
    }
    """
    try:
        # Parse departure/arrival time if provided
        departure_time = None
        arrival_time = None
        
        if request.departure_time:
            try:
                departure_time = datetime.fromisoformat(request.departure_time)
            except ValueError:
                departure_time = datetime.now()
        
        if request.arrival_time:
            try:
                arrival_time = datetime.fromisoformat(request.arrival_time)
            except ValueError:
                pass
        
        # Build directions request parameters
        params = {
            "origin": request.origin,
            "destination": request.destination,
            "mode": request.mode,
            "alternatives": request.alternatives
        }
        
        # Add optional parameters
        if departure_time:
            params["departure_time"] = departure_time
        if arrival_time:
            params["arrival_time"] = arrival_time
        if request.avoid:
            params["avoid"] = request.avoid
        
        
        # Get directions
        directions_result = gmaps.directions(**params)
        
        if not directions_result:
            raise HTTPException(
                status_code=404,
                detail=f"No route found from {request.origin} to {request.destination}"
            )
        
        # Parse and format the response
        routes = []
        for route in directions_result:
            legs = []
            for leg in route.get('legs', []):
                steps = []
                for step in leg.get('steps', []):
                    steps.append({
                        "instruction": step.get('html_instructions', ''),
                        "distance": step.get('distance', {}).get('text', ''),
                        "duration": step.get('duration', {}).get('text', ''),
                        "travel_mode": step.get('travel_mode', ''),
                        "start_location": step.get('start_location', {}),
                        "end_location": step.get('end_location', {})
                    })
                
                legs.append({
                    "start_address": leg.get('start_address', ''),
                    "end_address": leg.get('end_address', ''),
                    "distance": leg.get('distance', {}).get('text', ''),
                    "duration": leg.get('duration', {}).get('text', ''),
                    "steps": steps
                })
            
            routes.append({
                "summary": route.get('summary', ''),
                "legs": legs,
                "overview_polyline": route.get('overview_polyline', {}).get('points', ''),
                "warnings": route.get('warnings', []),
                "waypoint_order": route.get('waypoint_order', [])
            })
        
        
        return {
            "origin": request.origin,
            "destination": request.destination,
            "mode": request.mode,
            "routes": routes,
            "routes_count": len(routes)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting directions: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get directions: {str(e)}"
        )


@router.get("/distance-matrix")
async def get_distance_matrix(
    origins: str,
    destinations: str,
    mode: str = "driving",
    current_user: schemas.UserResponse = Depends(get_current_active_user),
    gmaps: googlemaps.Client = Depends(get_gmaps_client)
):
    """
    Get distance and duration between multiple origins and destinations
    
    Args:
        origins: Pipe-separated list of origins (e.g., "Paris|Lyon")
        destinations: Pipe-separated list of destinations (e.g., "Berlin|Munich")
        mode: Travel mode (driving, walking, bicycling, transit)
    
    Example:
        /distance-matrix?origins=Paris,France&destinations=London,UK&mode=driving
    """
    try:
        origins_list = origins.split('|')
        destinations_list = destinations.split('|')
        
        
        result = gmaps.distance_matrix(
            origins=origins_list,
            destinations=destinations_list,
            mode=mode
        )
        
        # Format response
        matrix = []
        for i, row in enumerate(result.get('rows', [])):
            for j, element in enumerate(row.get('elements', [])):
                if element.get('status') == 'OK':
                    matrix.append({
                        "origin": result['origin_addresses'][i],
                        "destination": result['destination_addresses'][j],
                        "distance": element.get('distance', {}).get('text', 'N/A'),
                        "distance_value": element.get('distance', {}).get('value', 0),
                        "duration": element.get('duration', {}).get('text', 'N/A'),
                        "duration_value": element.get('duration', {}).get('value', 0)
                    })
        
        return {
            "mode": mode,
            "matrix": matrix,
            "origin_addresses": result.get('origin_addresses', []),
            "destination_addresses": result.get('destination_addresses', [])
        }
        
    except Exception as e:
        logger.error(f"Error getting distance matrix: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get distance matrix: {str(e)}"
        )


@router.get("/reverse-geocode")
async def reverse_geocode(
    lat: float,
    lng: float,
    current_user: schemas.UserResponse = Depends(get_current_active_user),
    gmaps: googlemaps.Client = Depends(get_gmaps_client)
):
    """
    Convert coordinates to address (reverse geocoding)
    
    Args:
        lat: Latitude
        lng: Longitude
    
    Example:
        /reverse-geocode?lat=48.8584&lng=2.2945
    """
    try:
        
        result = gmaps.reverse_geocode((lat, lng))
        
        if not result:
            raise HTTPException(
                status_code=404,
                detail=f"No address found for coordinates ({lat}, {lng})"
            )
        
        # Get the most relevant result
        primary_result = result[0]
        
        return {
            "lat": lat,
            "lng": lng,
            "formatted_address": primary_result.get('formatted_address', ''),
            "place_id": primary_result.get('place_id', ''),
            "types": primary_result.get('types', []),
            "address_components": primary_result.get('address_components', []),
            "all_results": [
                {
                    "formatted_address": r.get('formatted_address', ''),
                    "types": r.get('types', [])
                }
                for r in result[:5]  # Return top 5 results
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reverse geocoding: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to reverse geocode: {str(e)}"
        )
