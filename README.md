# 🌍 AI Travel Planner - Complete Backend API

An intelligent travel planning API powered by AI agents that creates comprehensive travel itineraries with real-time data integration.

## ✨ Features

### 🎯 Core Travel Planning
- **AI-Powered Itineraries**: Complete day-by-day travel plans with tourist and offbeat routes
- **Smart Recommendations**: Hotels, restaurants, attractions, and activities
- **Budget Planning**: Detailed cost breakdowns with currency conversion
- **Weather Integration**: Real-time weather data and seasonal recommendations

### 🔧 API Services
- **Travel Planning**: `/query`, `/plan-trip` - Comprehensive travel plan generation
- **Weather Service**: `/weather/*` - Current conditions and forecasts
- **Currency Conversion**: `/currency/*` - Real-time exchange rates
- **Place Discovery**: `/places/*` - Attractions, restaurants, activities search
- **File Management**: Export and download travel plans as Markdown files

### 🏗️ Technical Features
- **FastAPI Framework**: High-performance async API with automatic documentation
- **AI Agent Workflow**: LangGraph-powered multi-tool agent system
- **Real-time Data**: Integration with multiple external APIs
- **Docker Support**: Container-ready with Docker Compose configuration
- **Comprehensive Logging**: Structured logging with rotation
- **Rate Limiting**: Built-in request throttling
- **Error Handling**: Graceful error management with detailed responses

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Required API keys (see Environment Setup)

### 1. Clone and Setup
```bash
# Clone the repository
git clone <your-repo-url>
cd AI_Travel_Planner

# Create virtual environment
python -m venv env
source env/bin/activate  # On Windows: env\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Setup
```bash
# Copy environment template
cp .env.template .env

# Edit .env with your API keys
nano .env  # or use your preferred editor
```

**Required API Keys:**
- **GROQ_API_KEY**: Get from [Groq Console](https://console.groq.com/keys)
- **OPENWEATHERMAP_API_KEY**: Get from [OpenWeatherMap](https://openweathermap.org/api)
- **GPLACES_API_KEY**: Get from [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
- **TAVILY_API_KEY**: Get from [Tavily](https://app.tavily.com/)
- **EXCHANGE_RATE_API_KEY**: Get from [ExchangeRate-API](https://exchangerate-api.com/)

### 3. Start the Application

#### Option A: Using the Startup Script (Recommended)
```bash
# Development mode (with auto-reload)
python start.py dev

# Production mode
python start.py prod

# Docker mode
python start.py docker

# Check configuration
python start.py check
```

#### Option B: Direct Commands
```bash
# Development
uvicorn main:app --reload --port 8000

# Production
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

#### Option C: Docker Compose
```bash
docker-compose up --build
```

### 4. Access the API
- **API Documentation**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## 📚 API Usage

### Basic Travel Planning
```python
import requests

# Simple query
response = requests.post("http://localhost:8000/query", json={
    "question": "Plan a 5-day trip to Paris with $2000 budget"
})

print(response.json()["answer"])
```

### Detailed Planning
```python
# Detailed planning with specific parameters
response = requests.post("http://localhost:8000/plan-trip", json={
    "destination": "Tokyo, Japan",
    "duration": 7,
    "budget": "$3000",
    "preferences": ["cultural", "food", "technology"],
    "group_size": 2,
    "currency": "USD"
})
```

### Weather Information
```python
# Get current weather
response = requests.post("http://localhost:8000/weather/current", json={
    "city": "London"
})

# Get weather forecast
response = requests.get("http://localhost:8000/weather/forecast/London")
```

### Currency Conversion
```python
# Convert currency
response = requests.post("http://localhost:8000/currency/convert", json={
    "amount": 1000,
    "from_currency": "USD",
    "to_currency": "EUR"
})

# Get exchange rates
response = requests.get("http://localhost:8000/currency/rates/USD")
```

## 🏗️ Project Structure

```
AI_Travel_Planner/
├── api/                    # API layer
│   ├── __init__.py
│   ├── models.py          # Pydantic models
│   ├── dependencies.py    # Dependency injection
│   └── routes.py          # Additional route handlers
├── agent/                 # AI Agent system
│   ├── __init__.py
│   └── agentic_workflow.py # LangGraph workflow
├── tools/                 # AI Tools
│   ├── weather_info_tool.py
│   ├── place_search_tool.py
│   ├── currency_conversion_tool.py
│   └── expense_calculator_tool.py
├── utils/                 # Utility functions
│   ├── model_loader.py
│   ├── weather_info.py
│   ├── place_info_search.py
│   ├── currency_converter.py
│   ├── expense_calculator.py
│   └── save_to_document.py
├── core/                  # Core configuration
│   ├── __init__.py
│   ├── config.py         # Settings management
│   └── logging_config.py # Logging setup
├── config/               # Configuration files
│   └── config.yaml
├── prompt_library/       # AI prompts
│   └── prompt.py
├── main.py              # FastAPI application
├── start.py             # Startup script
├── streamlit_app.py     # Web interface
├── Dockerfile           # Docker configuration
├── docker-compose.yml   # Docker Compose setup
├── requirements.txt     # Python dependencies
└── .env.template       # Environment template
```

## 🛠️ Development

### Adding New Features
1. **New API Endpoints**: Add to `api/routes.py`
2. **New AI Tools**: Create in `tools/` directory
3. **New Models**: Add to `api/models.py`
4. **Configuration**: Update `core/config.py`

### Testing
```bash
# Run all tests
python start.py test

# Manual testing of tools (debug mode only)
curl http://localhost:8000/debug/test-tools
```

### Logging
- **Application logs**: `./logs/travel_planner.log`
- **Error logs**: `./logs/error.log`
- **Log level**: Configurable via `LOG_LEVEL` environment variable

## 🐳 Docker Deployment

### Build and Run
```bash
# Build image
docker build -t ai-travel-planner .

# Run container
docker run -p 8000:8000 --env-file .env ai-travel-planner

# Or use Docker Compose
docker-compose up --build
```

### Production Deployment
```bash
# Set environment to production
echo "ENVIRONMENT=production" >> .env

# Use production settings
docker-compose -f docker-compose.yml up -d
```

## 📊 Monitoring and Analytics

### API Statistics
- **Endpoint**: `/analytics/stats`
- **Health Check**: `/analytics/health-detailed`
- **System Status**: `/status`

### Available Metrics
- Total queries processed
- Success/error rates
- Popular destinations
- System uptime
- Service health status

## 🔒 Security Features

- **Rate Limiting**: 60 requests/minute per IP (configurable)
- **API Key Support**: Optional API key authentication
- **CORS Configuration**: Configurable allowed origins
- **Input Validation**: Pydantic model validation
- **Error Sanitization**: Secure error messages

## 🌍 Supported Features

### Destinations
- **Global Coverage**: Worldwide destination support
- **150+ Currencies**: Real-time conversion
- **Weather Data**: Global weather information
- **Multi-language**: Place names in various languages

### Travel Categories
- Beach destinations
- Mountain adventures
- City breaks
- Cultural heritage sites
- Adventure travel
- Romantic getaways
- Family-friendly locations
- Budget-friendly options

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 📞 Support

- **Issues**: Create a GitHub issue
- **Documentation**: Visit `/docs` endpoint when running
- **Email**: support@example.com

## 🔄 Version History

- **v1.0.0**: Initial release with full API functionality
  - Complete AI agent integration
  - Multi-service architecture
  - Docker support
  - Comprehensive documentation

## 🎯 Roadmap

### Phase 2 (Coming Soon)
- [ ] **Database Integration**: PostgreSQL for plan storage and user management
- [ ] **User Authentication**: JWT-based user system
- [ ] **Plan Sharing**: Share travel plans with others
- [ ] **Booking Integration**: Direct hotel and flight booking
- [ ] **Mobile App**: React Native companion app

### Phase 3 (Future)
- [ ] **AI Personalization**: Learn from user preferences
- [ ] **Group Planning**: Collaborative trip planning
- [ ] **Expense Tracking**: Real-time expense tracking during trips
- [ ] **Photo Integration**: AI-powered photo recommendations
- [ ] **Social Features**: Travel community and reviews

## 🧪 Example API Responses

### Travel Plan Response
```json
{
  "answer": "# 🌍 Complete Paris Travel Plan\n\n## Overview\nA comprehensive 5-day journey through Paris...",
  "status": "success",
  "timestamp": "2024-01-15T10:30:00Z",
  "query": "Plan a 5-day trip to Paris with $2000 budget"
}
```

### Weather Response
```json
{
  "city": "Paris",
  "current_weather": {
    "description": "Current weather in Paris: 18°C, partly cloudy"
  },
  "forecast": [
    {
      "description": "Weather forecast for Paris:\n2024-01-16: 16°C, light rain\n2024-01-17: 19°C, sunny"
    }
  ],
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Currency Conversion Response
```json
{
  "original_amount": 1000.0,
  "converted_amount": 850.0,
  "from_currency": "USD",
  "to_currency": "EUR",
  "exchange_rate": 0.85,
  "timestamp": "2024-01-15T10:30:00Z"
}
```

## 🔧 Troubleshooting

### Common Issues

#### 1. API Key Errors
```bash
# Check if API keys are properly set
python start.py check

# Verify .env file exists and has correct keys
cat .env | grep API_KEY
```

#### 2. Module Import Errors
```bash
# Reinstall dependencies
pip install -r requirements.txt

# Check Python path
python -c "import sys; print(sys.path)"
```

#### 3. Port Already in Use
```bash
# Kill process using port 8000
lsof -ti:8000 | xargs kill -9

# Or use a different port
uvicorn main:app --port 8001
```

<!-- #### 4. Docker Issues
```bash
# Clean Docker cache
docker system prune -a

# Rebuild without cache
docker-compose build --no-cache
``` -->

<!-- ### Debug Mode
Enable debug mode for detailed error information:
```bash
# In .env file
DEBUG=True
LOG_LEVEL=DEBUG

# Restart the application
python start.py dev -->
<!-- ``` -->

## 📈 Performance Optimization

### Production Settings
```python
# In .env for production
ENVIRONMENT=production
DEBUG=False
LOG_LEVEL=WARNING
RATE_LIMIT_PER_MINUTE=30
```

### Scaling Options
1. **Horizontal Scaling**: Multiple container instances
2. **Load Balancer**: Nginx reverse proxy
3. **Caching**: Redis for API response caching
4. **Database**: PostgreSQL for persistent storage

### Resource Requirements
- **Minimum**: 1GB RAM, 1 CPU core
- **Recommended**: 2GB RAM, 2 CPU cores
- **Storage**: 1GB for logs and generated files

## 🛡️ Security Best Practices

1. **Environment Variables**: Never commit API keys to git
2. **HTTPS**: Use SSL certificates in production
3. **Rate Limiting**: Configure appropriate limits
4. **Input Validation**: All inputs are validated
5. **Error Handling**: Sensitive information is not exposed

## 📋 API Endpoint Reference

### Travel Planning
- `POST /query` - Simple travel planning
- `POST /plan-trip` - Detailed travel planning

### Weather Services
- `POST /weather/current` - Current weather
- `GET /weather/forecast/{city}` - Weather forecast

### Currency Services
- `POST /currency/convert` - Currency conversion
- `GET /currency/rates/{base}` - Exchange rates

### Place Discovery
- `POST /places/search` - Search places
- `GET /places/popular` - Popular destinations

### Information
- `GET /destinations` - Destination categories
- `GET /travel-tips` - Travel advice

### File Management
- `GET /download-plan/{filename}` - Download plan
- `GET /list-plans` - List saved plans

### System
- `GET /health` - Health check
- `GET /status` - System status
- `GET /analytics/stats` - API statistics

---

## 🙏 Acknowledgments

- **LangChain**: For the AI agent framework
- **FastAPI**: For the high-performance web framework
- **OpenWeatherMap**: For weather data
- **Google Places**: For location information
- **Groq**: For fast AI inference
- **All Contributors**: Thanks to everyone who helped build this!

---

AI-TRAVEL-PLANNER/
│
├── 📁 agent/                          # AI Agent Core Logic
│   ├── __init__.py
│   └── agentic_workflow.py           # LangGraph-based agent workflow
│
├── 📁 api/                            # FastAPI REST API Layer
│   ├── __init__.py
│   ├── dependencies.py               # Dependency injection, rate limiting, auth
│   ├── models.py                     # Pydantic request/response models
│   ├── routes.py                     # Additional API routes (weather, currency, places)
│   └── routes/
│       └── places.py                 # Places-specific routes
│
├── 📁 core/                           # Core Configuration
│   ├── __init__.py
│   ├── config.py                     # Settings management (Pydantic BaseSettings)
│   └── logging_config.py             # Logging setup and middleware
│
├── 📁 tools/                          # LangChain Tools (Agent Actions)
│   ├── __init__.py
│   ├── weather_info_tool.py          # Weather API tools
│   ├── place_search_tool.py          # Google Places & Tavily search tools
│   ├── currency_conversion_tool.py   # Currency conversion tools
│   ├── expense_calculator_tool.py    # Cost calculation tools
│   └── arthamatic_op_tool.py         # Basic arithmetic operations
│
├── 📁 utils/                          # Utility Functions
│   ├── __init__.py
│   ├── model_loader.py               # LLM loading (Groq/OpenAI)
│   ├── weather_info.py               # Weather API wrapper
│   ├── place_info_search.py          # Places search wrappers
│   ├── currency_converter.py         # Currency conversion logic
│   ├── expense_calculator.py         # Cost calculation logic
│   ├── save_to_document.py           # Export travel plans to Markdown
│   └── config_loader.py              # YAML config loader
│
├── 📁 prompt_library/                 # Prompt Engineering
│   ├── __init__.py
│   └── prompt.py                     # System prompts for AI agent
│
├── 📁 config/                         # Configuration Files
│   ├── __init__.py
│   └── config.yaml                   # Model configurations
│
├── 📁 tests/                          # Test Suite
│   ├── __init__.py
│   ├── conftest.py                   # Pytest fixtures
│   ├── test_api.py                   # API endpoint tests
│   └── test_places.py                # Places service tests
│
├── 📁 notebook/                       # Jupyter Notebooks
│   └── experiments.ipynb             # Development experiments
│
├── 📁 output/                         # Generated Travel Plans (Markdown files)
├── 📁 graphs/                         # Agent graph visualizations
├── 📁 logs/                           # Application logs
│
├── 📄 main.py                         # FastAPI Application Entry Point
├── 📄 streamlit_app.py               # Streamlit UI (alternative interface)
├── 📄 start.py                        # Startup script with multiple modes
├── 📄 requirements.txt               # Python dependencies
├── 📄 setup.py                        # Package setup
├── 📄 pyproject.toml                 # Modern Python project config
├── 📄 .env                            # Environment variables (API keys)
├── 📄 .gitignore                     # Git ignore rules
└── 📄 README.md                       # Project documentation

*Built with ❤️ for travelers worldwide*
