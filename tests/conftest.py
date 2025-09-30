import pytest
from fastapi.testclient import TestClient
from dotenv import load_dotenv
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables from .env
load_dotenv()

@pytest.fixture(scope="session", autouse=True)
def verify_environment():
    """Verify all required API keys are present"""
    required_vars = {
        "GROQ_API_KEY": "Groq AI (required for LLM)",
        "GPLACES_API_KEY": "Google Places (required for place search)",
        "TAVILY_API_KEY": "Tavily Search (required for backup search)",
        "OPENWEATHERMAP_API_KEY": "OpenWeatherMap (required for weather)",
        "EXCHANGE_RATE_API_KEY": "ExchangeRate API (required for currency)"
    }
    
    missing = []
    for var, description in required_vars.items():
        if not os.getenv(var):
            missing.append(f"{var} ({description})")
    
    if missing:
        print("\n" + "="*70)
        print("⚠️  MISSING API KEYS - Tests will fail!")
        print("="*70)
        for item in missing:
            print(f"  ❌ {item}")
        print("\n📝 Please add these keys to your .env file")
        print("💡 See the API Key Setup Guide for instructions")
        print("="*70 + "\n")
        pytest.exit("Missing required API keys. See message above.")
    
    print("\n" + "="*70)
    print("✅ All required API keys found")
    print("="*70)
    print(f"  ✓ Groq API Key: {os.getenv('GROQ_API_KEY')[:10]}...")
    print(f"  ✓ Google Places Key: {os.getenv('GPLACES_API_KEY')[:10]}...")
    print(f"  ✓ Tavily Key: {os.getenv('TAVILY_API_KEY')[:10]}...")
    print(f"  ✓ Weather Key: {os.getenv('OPENWEATHERMAP_API_KEY')[:10]}...")
    print(f"  ✓ Currency Key: {os.getenv('EXCHANGE_RATE_API_KEY')[:10]}...")
    api_key = os.getenv('API_KEY')
    if api_key:
        print(f"  ✓ API Key Protection: Enabled ({api_key[:10]}...)")
    else:
        print(f"  ℹ️  API Key Protection: Disabled (all endpoints open)")
    print("="*70 + "\n")
    
    yield

@pytest.fixture
def client():
    """Create FastAPI test client"""
    from main import app
    return TestClient(app)

@pytest.fixture
def auth_headers():
    """
    Authentication headers for protected endpoints
    Returns headers dict with API key if configured, empty dict otherwise
    """
    api_key = os.getenv("API_KEY", "")
    if api_key:
        return {"X-API-Key": api_key}
    return {}

