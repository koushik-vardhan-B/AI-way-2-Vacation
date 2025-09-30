import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from main import app

@pytest.fixture
def client():
    return TestClient(app)

def test_places_search(client):
    with patch('langchain_community.utilities.tavily_search.TavilySearchAPIWrapper.run') as mock_search:
        mock_search.return_value = [{"title": "Test Place", "snippet": "Test Description"}]
        response = client.get("/places/search/Paris")
        assert response.status_code == 200
        assert "results" in response.json()