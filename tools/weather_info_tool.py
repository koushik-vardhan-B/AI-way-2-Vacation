import os
from utils.weather_info import WeatherForecastTool
from langchain.tools import tool
from typing import List
from dotenv import load_dotenv

class WeatherInfoTool:
    def __init__(self):
        load_dotenv()
        self.api_key = os.environ.get("OPENWEATHERMAP_API_KEY")
        self.weather_service = WeatherForecastTool(self.api_key)
        self.weather_tool_list = self._setup_tools()
    
    def _setup_tools(self) -> List:
        """Setup all tools for the weather forecast tool"""
        
        @tool
        def get_current_weather(city: str) -> str:
            """Get current weather for a city with temperature in Celsius"""
            weather_data = self.weather_service.get_current_weather(city)
            if weather_data and 'main' in weather_data:
                temp = weather_data.get('main', {}).get('temp', 'N/A')
                feels_like = weather_data.get('main', {}).get('feels_like', 'N/A')
                humidity = weather_data.get('main', {}).get('humidity', 'N/A')
                desc = weather_data.get('weather', [{}])[0].get('description', 'N/A')
                
                # Format temperature properly
                if temp != 'N/A':
                    temp = round(float(temp), 1)
                if feels_like != 'N/A':
                    feels_like = round(float(feels_like), 1)
                
                return (
                    f"Current weather in {city}:\n"
                    f"- Temperature: {temp}°C\n"
                    f"- Feels like: {feels_like}°C\n"
                    f"- Conditions: {desc}\n"
                    f"- Humidity: {humidity}%"
                )
            return f"Could not fetch weather for {city}"
        
        @tool
        def get_weather_forecast(city: str) -> str:
            """Get 5-day weather forecast for a city"""
            forecast_data = self.weather_service.get_forecast_weather(city)
            if forecast_data and 'list' in forecast_data:
                forecast_summary = []
                current_date = None
                
                for item in forecast_data['list']:
                    date = item['dt_txt'].split(' ')[0]
                    time = item['dt_txt'].split(' ')[1]
                    temp = round(float(item['main']['temp']), 1)
                    desc = item['weather'][0]['description']
                    
                    # Group by date for cleaner output
                    if date != current_date:
                        if current_date:  # Not the first entry
                            forecast_summary.append("")  # Add spacing between days
                        current_date = date
                        forecast_summary.append(f"**{date}**")
                    
                    forecast_summary.append(f"  {time}: {temp}°C, {desc}")
                
                return f"5-day weather forecast for {city}:\n" + "\n".join(forecast_summary)
            return f"Could not fetch forecast for {city}"
    
        return [get_current_weather, get_weather_forecast]