# Replace the content in tools/place_search_tool.py

import os
from utils.place_info_search import GooglePlaceSearchTool, TavilyPlaceSearchTool
from typing import List
from langchain.tools import tool
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

class PlaceSearchTool:
    def __init__(self):
        load_dotenv()
        self.google_api_key = os.environ.get("GPLACES_API_KEY")
        self.google_places_search = GooglePlaceSearchTool(self.google_api_key)
        self.tavily_search = TavilyPlaceSearchTool()
        self.place_search_tool_list = self._setup_tools()

    def _setup_tools(self) -> List:
        """Setup all tools for the place search tool"""
        @tool
        def search_attractions(place: str) -> str:
            """Search attractions of a place"""
            try:
                logger.info(f"🔍 Searching attractions for: {place}")
                attraction_result = self.google_places_search.google_search_attractions(place)
                if attraction_result:
                    return f"Following are the attractions of {place} as suggested by Google: {attraction_result}"
            except Exception as e:
                logger.warning(f"⚠️ Google Places failed for attractions: {e}")
                try:
                    logger.info(f"🔄 Falling back to Tavily for attractions in {place}")
                    tavily_result = self.tavily_search.tavily_search_attractions(place)
                    return f"Following are the attractions of {place}: {tavily_result}"
                except Exception as tavily_error:
                    logger.error(f"❌ Both Google and Tavily failed: {tavily_error}")
                    return f"Unable to fetch attractions for {place}. Please try searching online for '{place} tourist attractions'."
        
        @tool
        def search_restaurants(place: str) -> str:
            """Search restaurants of a place"""
            try:
                logger.info(f"🔍 Searching restaurants for: {place}")
                restaurants_result = self.google_places_search.google_search_restaurants(place)
                if restaurants_result:
                    return f"Following are the restaurants of {place} as suggested by Google: {restaurants_result}"
            except Exception as e:
                logger.warning(f"⚠️ Google Places failed for restaurants: {e}")
                try:
                    logger.info(f"🔄 Falling back to Tavily for restaurants in {place}")
                    tavily_result = self.tavily_search.tavily_search_restaurants(place)
                    return f"Following are the restaurants of {place}: {tavily_result}"
                except Exception as tavily_error:
                    logger.error(f"❌ Both Google and Tavily failed: {tavily_error}")
                    return f"Unable to fetch restaurants for {place}. Please try searching online for '{place} best restaurants'."
        
        @tool
        def search_activities(place: str) -> str:
            """Search activities of a place"""
            try:
                logger.info(f"🔍 Searching activities for: {place}")
                activities_result = self.google_places_search.google_search_activity(place)
                if activities_result:
                    return f"Following are the activities in and around {place} as suggested by Google: {activities_result}"
            except Exception as e:
                logger.warning(f"⚠️ Google Places failed for activities: {e}")
                try:
                    logger.info(f"🔄 Falling back to Tavily for activities in {place}")
                    tavily_result = self.tavily_search.tavily_search_activity(place)
                    return f"Following are the activities of {place}: {tavily_result}"
                except Exception as tavily_error:
                    logger.error(f"❌ Both Google and Tavily failed: {tavily_error}")
                    return f"Unable to fetch activities for {place}. Please try searching online for '{place} things to do'."
        
        @tool
        def search_transportation(place: str) -> str:
            """Search transportation of a place"""
            try:
                logger.info(f"🔍 Searching transportation for: {place}")
                transportation_result = self.google_places_search.google_search_transportation(place)
                if transportation_result:
                    return f"Following are the modes of transportation available in {place} as suggested by Google: {transportation_result}"
            except Exception as e:
                logger.warning(f"⚠️ Google Places failed for transportation: {e}")
                try:
                    logger.info(f"🔄 Falling back to Tavily for transportation in {place}")
                    tavily_result = self.tavily_search.tavily_search_transportation(place)
                    return f"Following are the modes of transportation available in {place}: {tavily_result}"
                except Exception as tavily_error:
                    logger.error(f"❌ Both Google and Tavily failed: {tavily_error}")
                    return f"Unable to fetch transportation info for {place}. Please try searching online for '{place} transportation guide'."
        
        return [search_attractions, search_restaurants, search_activities, search_transportation]
    
    def get_tools(self) -> List:
        """Return the list of tools - for backward compatibility"""
        return self.place_search_tool_list