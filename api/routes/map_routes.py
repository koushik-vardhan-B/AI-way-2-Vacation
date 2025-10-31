from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import googlemaps
import logging
from pydantic import BaseModel

from database import crud, schemas
from database.base import get_db
from api.auth import get_current_active_user
from core.config import get_settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/maps", tags=["🗺️ Maps"])


class LocationData(BaseModel):
    """Location data with coordinates"""
    name: str
    address: Optional[str] = None
    lat: float
    lng: float
    place_id: Optional[str] = None
    rating: Optional[float] = None
    types: Optional[List[str]] = None
    photo_reference: Optional[str] = None


class MapDataResponse(BaseModel):
    """Response containing map data for a destination"""
    destination: str
    center: Dict[str, float]  # {lat, lng}
    attractions: List[LocationData]
    restaurants: List[LocationData]
    hotels: List[LocationData]


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


@router.get("/location/{place_name}", response_model=LocationData)
async def get_location_coordinates(
    place_name: str,
    current_user: schemas.UserResponse = Depends(get_current_active_user),
    gmaps: googlemaps.Client = Depends(get_gmaps_client)
):
    """
    Get coordinates for a specific place name
    
    Returns latitude, longitude, and other location details
    """
    try:
        # Try geocoding first, fallback to places autocomplete if geocoding fails
        try:
            geocode_result = gmaps.geocode(place_name)
            
            if not geocode_result:
                raise ValueError("No geocode results")
            
            result = geocode_result[0]
            location = result['geometry']['location']
            
            return LocationData(
                name=result.get('formatted_address', place_name),
                address=result.get('formatted_address'),
                lat=location['lat'],
                lng=location['lng'],
                place_id=result.get('place_id'),
                types=result.get('types', [])
            )
        except Exception as geocode_error:
            logger.warning(f"Geocoding failed for {place_name}, trying places autocomplete: {geocode_error}")
            # Fallback to places autocomplete
            autocomplete_result = gmaps.places_autocomplete(input_text=place_name)
            
            if not autocomplete_result:
                raise HTTPException(
                    status_code=404,
                    detail=f"Location not found: {place_name}"
                )
            
            place_id = autocomplete_result[0]["place_id"]
            place_result = gmaps.place(
                place_id=place_id,
                fields=["name", "formatted_address", "geometry", "types"]
            )
            
            result = place_result["result"]
            location = result['geometry']['location']
            
            return LocationData(
                name=result.get('formatted_address', place_name),
                address=result.get('formatted_address'),
                lat=location['lat'],
                lng=location['lng'],
                place_id=place_id,
                types=result.get('types', [])
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error geocoding {place_name}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get location data: {str(e)}"
        )


@router.get("/destination/{destination}", response_model=MapDataResponse)
async def get_destination_map_data(
    destination: str,
    radius: int = 5000,
    current_user: schemas.UserResponse = Depends(get_current_active_user),
    gmaps: googlemaps.Client = Depends(get_gmaps_client)
):
    """
    Get comprehensive map data for a destination including:
    - Main destination coordinates
    - Nearby attractions
    - Nearby restaurants
    - Nearby hotels
    
    Args:
        destination: Name of the destination
        radius: Search radius in meters (default: 5000m = 5km)
    """
    try:
        # Get destination coordinates
        # Try geocoding first, fallback to places autocomplete if geocoding fails
        try:
            geocode_result = gmaps.geocode(destination)
            if geocode_result:
                center_location = geocode_result[0]['geometry']['location']
                center = {"lat": center_location['lat'], "lng": center_location['lng']}
            else:
                raise ValueError("No geocode results")
        except Exception as geocode_error:
            logger.warning(f"Geocoding failed, trying places autocomplete: {geocode_error}")
            # Fallback to places autocomplete
            autocomplete_result = gmaps.places_autocomplete(
                input_text=destination,
                types=["(cities)"]
            )
            
            if not autocomplete_result:
                raise HTTPException(
                    status_code=404,
                    detail=f"Destination not found: {destination}"
                )
            
            place_id = autocomplete_result[0]["place_id"]
            place_result = gmaps.place(
                place_id=place_id,
                fields=["geometry"]
            )
            center_location = place_result["result"]["geometry"]["location"]
            center = {"lat": center_location['lat'], "lng": center_location['lng']}
        
        
        # Search for attractions
        attractions_raw = gmaps.places_nearby(
            location=center_location,
            radius=radius,
            type='tourist_attraction'
        )
        
        # Search for restaurants
        restaurants_raw = gmaps.places_nearby(
            location=center_location,
            radius=radius,
            type='restaurant'
        )
        
        # Search for hotels
        hotels_raw = gmaps.places_nearby(
            location=center_location,
            radius=radius,
            type='lodging'
        )
        
        # Parse attractions
        attractions = []
        for place in attractions_raw.get('results', [])[:20]:  # Limit to 20
            photo_ref = None
            if place.get('photos'):
                photo_ref = place['photos'][0].get('photo_reference')
            
            attractions.append(LocationData(
                name=place.get('name', 'Unknown'),
                address=place.get('vicinity'),
                lat=place['geometry']['location']['lat'],
                lng=place['geometry']['location']['lng'],
                place_id=place.get('place_id'),
                rating=place.get('rating'),
                types=place.get('types', []),
                photo_reference=photo_ref
            ))
        
        # Parse restaurants
        restaurants = []
        for place in restaurants_raw.get('results', [])[:20]:  # Limit to 20
            photo_ref = None
            if place.get('photos'):
                photo_ref = place['photos'][0].get('photo_reference')
            
            restaurants.append(LocationData(
                name=place.get('name', 'Unknown'),
                address=place.get('vicinity'),
                lat=place['geometry']['location']['lat'],
                lng=place['geometry']['location']['lng'],
                place_id=place.get('place_id'),
                rating=place.get('rating'),
                types=place.get('types', []),
                photo_reference=photo_ref
            ))
        
        # Parse hotels
        hotels = []
        for place in hotels_raw.get('results', [])[:15]:  # Limit to 15
            photo_ref = None
            if place.get('photos'):
                photo_ref = place['photos'][0].get('photo_reference')
            
            hotels.append(LocationData(
                name=place.get('name', 'Unknown'),
                address=place.get('vicinity'),
                lat=place['geometry']['location']['lat'],
                lng=place['geometry']['location']['lng'],
                place_id=place.get('place_id'),
                rating=place.get('rating'),
                types=place.get('types', []),
                photo_reference=photo_ref
            ))
        
        
        return MapDataResponse(
            destination=destination,
            center=center,
            attractions=attractions,
            restaurants=restaurants,
            hotels=hotels
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching map data for {destination}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get map data: {str(e)}"
        )


@router.get("/plan/{plan_id}/map-data", response_model=MapDataResponse)
async def get_plan_map_data(
    plan_id: int,
    radius: int = 5000,
    db: Session = Depends(get_db),
    current_user: schemas.UserResponse = Depends(get_current_active_user),
    gmaps: googlemaps.Client = Depends(get_gmaps_client)
):
    """
    Get map data for a specific travel plan
    
    Returns all location data needed to display the plan on a map
    """
    # Verify plan belongs to user
    plan = crud.get_travel_plan(db, plan_id=plan_id, user_id=current_user.id)
    
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Travel plan not found"
        )
    
    # Use the plan's destination to get map data
    return await get_destination_map_data(
        destination=plan.destination,
        radius=radius,
        current_user=current_user,
        gmaps=gmaps
    )


@router.get("/photo/{photo_reference}")
async def get_place_photo_url(
    photo_reference: str,
    max_width: int = 400,
    current_user: schemas.UserResponse = Depends(get_current_active_user)
):
    """
    Get Google Places photo URL
    
    Args:
        photo_reference: Photo reference from Places API
        max_width: Maximum width of the photo (default: 400px)
    
    Returns:
        URL to the photo
    """
    settings = get_settings()
    photo_url = (
        f"https://maps.googleapis.com/maps/api/place/photo"
        f"?maxwidth={max_width}"
        f"&photo_reference={photo_reference}"
        f"&key={settings.GOOGLE_API_KEY}"
    )
    
    return {"photo_url": photo_url}


@router.post("/search-nearby")
async def search_nearby_places(
    request: Dict[str, Any],
    current_user: schemas.UserResponse = Depends(get_current_active_user),
    gmaps: googlemaps.Client = Depends(get_gmaps_client)
):
    """
    Search for nearby places of a specific type
    
    Request body:
    {
        "lat": 40.7128,
        "lng": -74.0060,
        "type": "restaurant",  # or "cafe", "museum", etc.
        "radius": 1000,  # in meters
        "keyword": "italian"  # optional
    }
    """
    try:
        lat = request.get('lat')
        lng = request.get('lng')
        place_type = request.get('type', 'point_of_interest')
        radius = request.get('radius', 1000)
        keyword = request.get('keyword')
        
        if lat is None or lng is None:
            raise HTTPException(
                status_code=400,
                detail="Latitude and longitude are required"
            )
        
        location = {"lat": lat, "lng": lng}
        
        # Search nearby
        search_params = {
            "location": location,
            "radius": radius,
            "type": place_type
        }
        
        if keyword:
            search_params["keyword"] = keyword
        
        results = gmaps.places_nearby(**search_params)
        
        # Parse results
        places = []
        for place in results.get('results', [])[:20]:
            photo_ref = None
            if place.get('photos'):
                photo_ref = place['photos'][0].get('photo_reference')
            
            places.append({
                "name": place.get('name'),
                "address": place.get('vicinity'),
                "lat": place['geometry']['location']['lat'],
                "lng": place['geometry']['location']['lng'],
                "place_id": place.get('place_id'),
                "rating": place.get('rating'),
                "types": place.get('types', []),
                "photo_reference": photo_ref,
                "open_now": place.get('opening_hours', {}).get('open_now')
            })
        
        return {
            "query": {
                "location": location,
                "type": place_type,
                "radius": radius,
                "keyword": keyword
            },
            "results": places,
            "count": len(places)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching nearby places: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to search nearby places: {str(e)}"
        )
