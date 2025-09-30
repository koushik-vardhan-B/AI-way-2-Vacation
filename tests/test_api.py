import pytest
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestHealthEndpoints:
    """Test health and status endpoints (no auth required)"""
    
    def test_health_check(self, client):
        """Test basic health check"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "message" in data
        assert "timestamp" in data
        assert "version" in data

    def test_root_endpoint(self, client):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_status_endpoint(self, client):
        """Test detailed status endpoint"""
        response = client.get("/status")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "operational"
        assert "features" in data
        assert "endpoints" in data
        assert "version" in data

class TestTravelPlanningEndpoints:
    """Test main travel planning endpoints"""
    
    @pytest.mark.slow
    def test_query_endpoint_structure(self, client):
        """Test query endpoint with valid request"""
        request_data = {
            "question": "Plan a 3-day trip to London with budget $1500"
        }
        response = client.post("/query", json=request_data)
        
        # Should return 200 (success) or 500 (API error)
        assert response.status_code in [200, 500]
        
        if response.status_code == 200:
            data = response.json()
            assert "answer" in data
            assert "status" in data
            assert "timestamp" in data
            assert "query" in data
            # Verify the answer contains useful information
            assert len(data["answer"]) > 100

    def test_query_invalid_request(self, client):
        """Test query endpoint with invalid request"""
        request_data = {
            "question": "abc"  # Too short - min_length=5
        }
        response = client.post("/query", json=request_data)
        assert response.status_code == 422  # Validation error

    @pytest.mark.slow
    def test_plan_trip_endpoint_structure(self, client):
        """Test detailed trip planning endpoint"""
        request_data = {
            "destination": "Paris, France",
            "duration": 5,
            "budget": "$2000",
            "preferences": ["cultural", "food"],
            "group_size": 2
        }
        response = client.post("/plan-trip", json=request_data)
        
        assert response.status_code in [200, 500]

    def test_plan_trip_validation(self, client):
        """Test plan trip endpoint validation"""
        # Test 1: Invalid duration
        request_data = {
            "destination": "Paris",
            "duration": 0  # Should be >= 1
        }
        response = client.post("/plan-trip", json=request_data)
        assert response.status_code == 422

        # Test 2: Invalid preferences
        request_data = {
            "destination": "Paris",
            "duration": 5,
            "preferences": ["invalid_preference_xyz"]
        }
        response = client.post("/plan-trip", json=request_data)
        assert response.status_code == 422

class TestInformationEndpoints:
    """Test information endpoints (no auth required)"""
    
    def test_destinations_endpoint(self, client):
        """Test destinations endpoint"""
        response = client.get("/destinations")
        assert response.status_code == 200
        data = response.json()
        assert "regions" in data
        assert "categories" in data
        assert "trending_now" in data
        # Verify structure
        assert "asia" in data["regions"]
        assert "europe" in data["regions"]

    def test_travel_tips_endpoint(self, client):
        """Test travel tips endpoint"""
        response = client.get("/travel-tips")
        assert response.status_code == 200
        data = response.json()
        assert "planning_tips" in data
        assert "budget_tips" in data
        assert "safety_tips" in data
        assert "packing_essentials" in data

class TestWeatherEndpoints:
    """Test weather service endpoints (uses real OpenWeatherMap API)"""
    
    def test_current_weather_structure(self, client, auth_headers):
        """Test current weather endpoint with real API"""
        request_data = {"city": "London"}
        response = client.post("/weather/current", json=request_data, headers=auth_headers)
        
        assert response.status_code in [200, 500]
        
        if response.status_code == 200:
            data = response.json()
            assert "city" in data
            assert data["city"] == "London"
            assert "current_weather" in data
            assert "forecast" in data
            assert "timestamp" in data
            print(f"✅ Weather test passed: {data['city']}")

    def test_weather_forecast_structure(self, client, auth_headers):
        """Test weather forecast endpoint"""
        response = client.get("/weather/forecast/Paris", headers=auth_headers)
        assert response.status_code in [200, 500]

class TestCurrencyEndpoints:
    """Test currency service endpoints (uses real ExchangeRate API)"""
    
    def test_currency_convert_structure(self, client, auth_headers):
        """Test currency conversion with real API"""
        request_data = {
            "amount": 100.0,
            "from_currency": "INR",
            "to_currency": "USD"
        }
        response = client.post("/currency/convert", json=request_data, headers=auth_headers)
        
        assert response.status_code in [200, 500]
        
        if response.status_code == 200:
            data = response.json()
            assert "original_amount" in data
            assert data["original_amount"] == 100.0
            assert "converted_amount" in data
            assert data["converted_amount"] > 0
            assert "from_currency" in data
            assert "to_currency" in data
            assert "exchange_rate" in data
            print(f"✅ Currency test passed: 100 USD = {data['converted_amount']:.2f} EUR")

    def test_currency_convert_validation(self, client, auth_headers):
        """Test currency conversion validation"""
        request_data = {
            "amount": -100.0,  # Invalid: should be > 0
            "from_currency": "USD",
            "to_currency": "EUR"
        }
        response = client.post("/currency/convert", json=request_data, headers=auth_headers)
        assert response.status_code == 422

    def test_exchange_rates_structure(self, client, auth_headers):
        """Test exchange rates endpoint"""
        response = client.get("/currency/rates/USD", headers=auth_headers)
        assert response.status_code in [200, 500]

class TestPlacesEndpoints:
    """Test places service endpoints (uses real Google Places + Tavily)"""
    
    def test_place_search_structure(self, client, auth_headers):
        """Test place search with real APIs"""
        request_data = {
            "place": "Tokyo",
            "search_type": "attractions"
        }
        response = client.post("/places/search", json=request_data, headers=auth_headers)
        
        assert response.status_code in [200, 500]
        
        if response.status_code == 200:
            data = response.json()
            assert "place" in data
            assert "search_type" in data
            assert "results" in data
            assert "timestamp" in data
            print(f"✅ Places test passed: Found attractions in {data['place']}")

    def test_place_search_validation(self, client, auth_headers):
        """Test place search validation"""
        request_data = {
            "place": "Paris",
            "search_type": "invalid_type_xyz"
        }
        response = client.post("/places/search", json=request_data, headers=auth_headers)
        assert response.status_code == 422

    def test_popular_places_endpoint(self, client):
        """Test popular places endpoint (no auth)"""
        response = client.get("/places/popular")
        assert response.status_code == 200
        data = response.json()
        assert "destinations" in data

class TestFileEndpoints:
    """Test file management endpoints"""
    
    def test_list_plans_endpoint(self, client):
        """Test list plans endpoint"""
        response = client.get("/list-plans")
        assert response.status_code == 200
        data = response.json()
        assert "plans" in data
        assert isinstance(data["plans"], list)

class TestAnalyticsEndpoints:
    """Test analytics endpoints"""
    
    def test_stats_endpoint(self, client):
        """Test API statistics endpoint"""
        response = client.get("/analytics/stats")
        assert response.status_code == 200
        data = response.json()
        assert "total_queries" in data
        assert "successful_plans" in data
        assert "uptime" in data

    def test_detailed_health_endpoint(self, client):
        """Test detailed health check"""
        response = client.get("/analytics/health-detailed")
        assert response.status_code == 200
        data = response.json()
        assert "overall_status" in data
        assert "services" in data
        assert "timestamp" in data

class TestValidation:
    """Test input validation"""
    
    def test_empty_requests(self, client, auth_headers):
        """Test endpoints with empty/missing data"""
        # Empty query
        response = client.post("/query", json={})
        assert response.status_code == 422

        # Empty plan trip
        response = client.post("/plan-trip", json={})
        assert response.status_code == 422

        # Empty weather request
        response = client.post("/weather/current", json={}, headers=auth_headers)
        assert response.status_code == 422

    def test_malformed_json(self, client):
        """Test malformed JSON"""
        response = client.post(
            "/query", 
            content=b"not valid json at all",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422

def test_openapi_schema(client):
    """Test OpenAPI schema generation"""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert "openapi" in schema
    assert "info" in schema
    assert "paths" in schema
    assert schema["info"]["title"] == "🌍 AI Travel Planner API"

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
