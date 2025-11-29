"""
Weather Tool for Agent Development Kit.
Provides weather data integration for context-aware scheduling.
"""

import requests
from datetime import datetime, date
from typing import Dict, Any, List, Optional
from tools.base_tool import BaseTool, ToolInput, ToolOutput

class WeatherTool(BaseTool):
    """
    Weather information tool for context-aware scheduling.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize weather tool.
        
        Args:
            api_key: OpenWeatherMap API key (optional, uses mock data if not provided)
        """
        super().__init__(
            name="weather_service",
            description="Get weather information for location-aware scheduling"
        )
        self.api_key = api_key
        self.base_url = "https://api.openweathermap.org/data/2.5"
    
    def execute(self, input_data: ToolInput) -> ToolOutput:
        """
        Execute weather query.
        
        Args:
            input_data: Weather query input
            
        Returns:
            Weather information result
        """
        self._log_usage()
        
        try:
            parameters = input_data.parameters or {}
            location = parameters.get('location', 'New York')
            query_type = input_data.query.lower()
            
            if 'current' in query_type or 'now' in query_type:
                return self._get_current_weather(location)
            elif 'forecast' in query_type:
                return self._get_forecast(location)
            elif 'outdoor' in query_type:
                return self._get_outdoor_conditions(location)
            else:
                return self._get_current_weather(location)
                
        except Exception as e:
            return ToolOutput(
                result=None,
                success=False,
                error_message=f"Weather query failed: {str(e)}",
                metadata={'location': location, 'query_type': input_data.query}
            )
    
    def _get_current_weather(self, location: str) -> ToolOutput:
        """Get current weather for location."""
        if not self.api_key:
            # Return mock data for demonstration
            return self._get_mock_weather(location)
        
        try:
            url = f"{self.base_url}/weather"
            params = {
                'q': location,
                'appid': self.api_key,
                'units': 'imperial'
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            weather_info = {
                'location': data['name'],
                'temperature': data['main']['temp'],
                'condition': data['weather'][0]['description'],
                'humidity': data['main']['humidity'],
                'wind_speed': data['wind']['speed'],
                'visibility': data.get('visibility', 10000) / 1000,  # km
                'timestamp': datetime.now().isoformat()
            }
            
            # Add scheduling recommendations
            recommendations = self._get_scheduling_recommendations(weather_info)
            
            return ToolOutput(
                result={
                    'weather': weather_info,
                    'scheduling_recommendations': recommendations
                },
                success=True,
                metadata={'source': 'OpenWeatherMap API'}
            )
            
        except requests.RequestException as e:
            return ToolOutput(
                result=None,
                success=False,
                error_message=f"Weather API request failed: {str(e)}",
                metadata={'location': location, 'api_endpoint': 'weather'}
            )
    
    def _get_forecast(self, location: str) -> ToolOutput:
        """Get weather forecast for location."""
        if not self.api_key:
            return self._get_mock_forecast(location)
        
        try:
            url = f"{self.base_url}/forecast"
            params = {
                'q': location,
                'appid': self.api_key,
                'units': 'imperial'
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            forecast_items = []
            for item in data['list'][:8]:  # Next 24 hours (3-hour intervals)
                forecast_items.append({
                    'datetime': item['dt_txt'],
                    'temperature': item['main']['temp'],
                    'condition': item['weather'][0]['description'],
                    'humidity': item['main']['humidity'],
                    'precipitation_probability': item.get('pop', 0) * 100
                })
            
            return ToolOutput(
                result={
                    'location': data['city']['name'],
                    'forecast': forecast_items
                },
                success=True,
                metadata={'source': 'OpenWeatherMap API'}
            )
            
        except requests.RequestException as e:
            return ToolOutput(
                result=None,
                success=False,
                error_message=f"Weather forecast request failed: {str(e)}",
                metadata={'location': location, 'api_endpoint': 'forecast'}
            )
    
    def _get_outdoor_conditions(self, location: str) -> ToolOutput:
        """Get outdoor activity suitability."""
        weather_result = self._get_current_weather(location)
        
        if not weather_result.success:
            return weather_result
        
        weather_data = weather_result.result['weather']
        
        # Analyze outdoor suitability
        outdoor_score = 10  # Start with perfect score
        warnings = []
        
        # Temperature checks
        temp = weather_data['temperature']
        if temp > 85:
            outdoor_score -= 3
            warnings.append("High temperature - consider indoor activities")
        elif temp < 32:
            outdoor_score -= 4
            warnings.append("Freezing temperature - dress warmly")
        elif temp < 50:
            outdoor_score -= 2
            warnings.append("Cold temperature - layer clothing")
        
        # Weather condition checks
        condition = weather_data['condition'].lower()
        if any(word in condition for word in ['rain', 'storm', 'drizzle']):
            outdoor_score -= 5
            warnings.append("Precipitation expected - bring umbrella or stay indoors")
        elif 'snow' in condition:
            outdoor_score -= 6
            warnings.append("Snow conditions - consider postponing outdoor activities")
        elif 'cloud' in condition:
            outdoor_score -= 1
        
        # Wind checks
        if weather_data['wind_speed'] > 20:
            outdoor_score -= 2
            warnings.append("High winds - secure loose items")
        
        outdoor_score = max(0, outdoor_score)
        
        suitability = "Excellent" if outdoor_score >= 8 else \
                     "Good" if outdoor_score >= 6 else \
                     "Fair" if outdoor_score >= 4 else \
                     "Poor"
        
        return ToolOutput(
            result={
                'location': weather_data['location'],
                'outdoor_score': outdoor_score,
                'suitability': suitability,
                'warnings': warnings,
                'current_weather': weather_data
            },
            success=True,
            metadata={'outdoor_analysis': True}
        )
    
    def _get_mock_weather(self, location: str) -> ToolOutput:
        """Generate mock weather data for demonstration."""
        import random
        
        conditions = [
            "clear sky", "few clouds", "scattered clouds", 
            "overcast clouds", "light rain", "moderate rain"
        ]
        
        weather_info = {
            'location': location,
            'temperature': random.randint(45, 85),
            'condition': random.choice(conditions),
            'humidity': random.randint(30, 90),
            'wind_speed': random.randint(0, 15),
            'visibility': random.uniform(5, 10),
            'timestamp': datetime.now().isoformat()
        }
        
        recommendations = self._get_scheduling_recommendations(weather_info)
        
        return ToolOutput(
            result={
                'weather': weather_info,
                'scheduling_recommendations': recommendations
            },
            success=True,
            metadata={'source': 'Mock Data'}
        )
    
    def _get_mock_forecast(self, location: str) -> ToolOutput:
        """Generate mock forecast data."""
        import random
        
        forecast_items = []
        base_temp = random.randint(60, 80)
        
        for i in range(8):
            temp_variation = random.randint(-10, 10)
            forecast_items.append({
                'datetime': (datetime.now() + datetime.timedelta(hours=i*3)).isoformat(),
                'temperature': base_temp + temp_variation,
                'condition': random.choice(["clear", "cloudy", "partly cloudy"]),
                'humidity': random.randint(40, 80),
                'precipitation_probability': random.randint(0, 30)
            })
        
        return ToolOutput(
            result={
                'location': location,
                'forecast': forecast_items
            },
            success=True,
            metadata={'source': 'Mock Data'}
        )
    
    def _get_scheduling_recommendations(self, weather_info: Dict[str, Any]) -> List[str]:
        """Generate scheduling recommendations based on weather."""
        recommendations = []
        
        temp = weather_info['temperature']
        condition = weather_info['condition'].lower()
        
        if temp > 85:
            recommendations.append("Schedule outdoor activities before 10am or after 6pm")
            recommendations.append("Plan indoor work during midday heat")
        elif temp < 45:
            recommendations.append("Allow extra time for travel and warm-up")
        
        if any(word in condition for word in ['rain', 'storm']):
            recommendations.append("Move outdoor meetings indoors")
            recommendations.append("Add buffer time for weather-related delays")
        elif 'clear' in condition:
            recommendations.append("Great day for outdoor meetings and activities")
        
        return recommendations