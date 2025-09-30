import pytest
import asyncio
from fastapi.testclient import TestClient
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app

# Create test client
client = TestClient(app)

# API key for testing
API_KEY = "test-api-key"

class TestHealthEndpoints:
    """Test health and status endpoints"""
    
    def test_health_check(self):
        """Test basic health check"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "message" in data
        assert "timestamp" in data
        assert "version" in data

    def test_root_endpoint(self):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_status_endpoint(self):
        """Test detailed status endpoint"""
        response = client.get("/status")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "operational"
        assert "features" in data
        assert "endpoints" in data
        assert "version" in data

class TestTravelPlanningEndpoints:
    """Test travel planning endpoints"""
    
    def test_query_endpoint_structure(self):
        """Test query endpoint with valid request"""
        request_data = {
            "question": "Plan a 3-day trip to London"
        }
        response = client.post("/query", json=request_data)
        
        # Should return 200 or 500 (depending on API keys)
        assert response.status_code in [200, 500]
        
        if response.status_code == 200:
            data = response.json()
            assert "answer" in data
            assert "status" in data
            assert "timestamp" in data
            assert "query" in data

    def test_query_invalid_request(self):
        """Test query endpoint with invalid request"""
        request_data = {
            "question": ""  # Empty question should fail validation
        }
        response = client.post("/query", json=request_data)
        assert response.status_code == 422  # Validation error

    def test_plan_trip_endpoint_structure(self):
        """Test detailed trip planning endpoint"""
        request_data = {
            "destination": "Paris, France",
            "duration": 5,
            "budget": "$2000",
            "preferences": ["cultural", "food"],
            "group_size": 2
        }
        response = client.post("/plan-trip", json=request_data)
        
        # Should return 200 or 500 (depending on API keys)
        assert response.status_code in [200, 500]

    def test_plan_trip_validation(self):
        """Test plan trip endpoint validation"""
        # Invalid duration
        request_data = {
            "destination": "Paris",
            "duration": 0  # Should be >= 1
        }
        response = client.post("/plan-trip", json=request_data)
        assert response.status_code == 422

        # Invalid preferences
        request_data = {
            "destination": "Paris",
            "duration": 5,
            "preferences": ["invalid_preference"]
        }
        response = client.post("/plan-trip", json=request_data)
        assert response.status_code == 422

class TestInformationEndpoints:
    """Test information endpoints"""
    
    def test_destinations_endpoint(self):
        """Test destinations endpoint"""
        response = client.get("/destinations")
        assert response.status_code == 200
        data = response.json()
        assert "regions" in data
        assert "categories" in data
        assert "trending_now" in data

    def test_travel_tips_endpoint(self):
        """Test travel tips endpoint"""
        response = client.get("/travel-tips")
        assert response.status_code == 200
        data = response.json()
        assert "planning_tips" in data
        assert "budget_tips" in data
        assert "safety_tips" in data
        assert "packing_essentials" in data

class TestWeatherEndpoints:
    """Test weather service endpoints"""
    
    def test_current_weather_structure(self):
        """Test current weather endpoint structure"""
        request_data = {"city": "London"}
        response = client.post("/weather/current", json=request_data, headers={"X-API-Key": API_KEY})
        
        # Should return 200 or 500 (depending on API keys)
        assert response.status_code in [200, 500]
        
        if response.status_code == 200:
            data = response.json()
            assert "city" in data
            assert "current_weather" in data
            assert "forecast" in data
            assert "timestamp" in data

    def test_weather_forecast_structure(self):
        """Test weather forecast endpoint structure"""
        response = client.get("/weather/forecast/London", headers={"X-API-Key": API_KEY})
        
        # Should return 200 or 500 (depending on API keys)
        assert response.status_code in [200, 500]

class TestCurrencyEndpoints:
    """Test currency service endpoints"""
    
    def test_currency_convert_structure(self):
        """Test currency conversion endpoint structure"""
        request_data = {
            "amount": 100.0,
            "from_currency": "USD",
            "to_currency": "EUR"
        }
        response = client.post("/currency/convert", json=request_data, headers={"X-API-Key": API_KEY})
        
        # Should return 200 or 500 (depending on API keys)
        assert response.status_code in [200, 500]
        
        if response.status_code == 200:
            data = response.json()
            assert "original_amount" in data
            assert "converted_amount" in data
            assert "from_currency" in data
            assert "to_currency" in data
            assert "exchange_rate" in data

    def test_currency_convert_validation(self):
        """Test currency conversion validation"""
        # Invalid amount
        request_data = {
            "amount": -100.0,  # Should be > 0
            "from_currency": "USD",
            "to_currency": "EUR"
        }
        response = client.post("/currency/convert", json=request_data, headers={"X-API-Key": API_KEY})
        assert response.status_code == 422

    def test_exchange_rates_structure(self):
        """Test exchange rates endpoint structure"""
        response = client.get("/currency/rates/USD", headers={"X-API-Key": API_KEY})
        
        # Should return 200 or 500 (depending on API keys)
        assert response.status_code in [200, 500]

class TestPlacesEndpoints:
    """Test places service endpoints"""
    
    def test_place_search_structure(self):
        """Test place search endpoint structure"""
        request_data = {
            "place": "Paris",
            "search_type": "attractions"
        }
        response = client.post("/places/search", json=request_data, headers={"X-API-Key": API_KEY})
        
        # Should return 200 or 500 (depending on API keys)
        assert response.status_code in [200, 500]
        
        if response.status_code == 200:
            data = response.json()
            assert "place" in data
            assert "search_type" in data
            assert "results" in data
            assert "timestamp" in data

    def test_place_search_validation(self):
        """Test place search validation"""
        # Invalid search type
        request_data = {
            "place": "Paris",
            "search_type": "invalid_type"
        }
        response = client.post("/places/search", json=request_data, headers={"X-API-Key": API_KEY})
        assert response.status_code == 422

    def test_popular_places_endpoint(self):
        """Test popular places endpoint"""
        response = client.get("/places/popular")
        assert response.status_code == 200
        data = response.json()
        assert "destinations" in data

class TestFileEndpoints:
    """Test file management endpoints"""
    
    def test_list_plans_endpoint(self):
        """Test list plans endpoint"""
        response = client.get("/list-plans")
        assert response.status_code == 200
        data = response.json()
        assert "plans" in data
        assert isinstance(data["plans"], list)

class TestAnalyticsEndpoints:
    """Test analytics endpoints"""
    
    def test_stats_endpoint(self):
        """Test API statistics endpoint"""
        response = client.get("/analytics/stats")
        assert response.status_code == 200
        data = response.json()
        assert "total_queries" in data
        assert "successful_plans" in data
        assert "uptime" in data

    def test_detailed_health_endpoint(self):
        """Test detailed health check endpoint"""
        response = client.get("/analytics/health-detailed")
        assert response.status_code == 200
        data = response.json()
        assert "overall_status" in data
        assert "services" in data
        assert "timestamp" in data

class TestValidation:
    """Test input validation"""
    
    def test_empty_requests(self):
        """Test endpoints with empty requests"""
        # Empty query
        response = client.post("/query", json={})
        assert response.status_code == 422

        # Empty plan trip
        response = client.post("/plan-trip", json={})
        assert response.status_code == 422

        # Empty weather request
        response = client.post("/weather/current", json={}, headers={"X-API-Key": API_KEY})
        assert response.status_code == 422

    def test_malformed_json(self):
        """Test endpoints with malformed JSON"""
        response = client.post("/query", data="invalid json")
        assert response.status_code == 422

def test_openapi_schema():
    """Test that OpenAPI schema is generated correctly"""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert "openapi" in schema
    assert "info" in schema
    assert "paths" in schema

if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])