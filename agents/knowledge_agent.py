"""
KnowledgeAgent - Fetches external insights like weather, research, and travel info.
This agent uses APIs and search to provide contextual information for scheduling.
"""

import json
import requests
from datetime import datetime
from typing import List, Dict, Any, Optional
from schemas.knowledge_schema import KnowledgeInsight
from tools.tool_registry import get_tool_registry
from tools.base_tool import ToolInput

class KnowledgeAgent:
    """
    KnowledgeAgent - Uses tools (APIs, search) to return structured insight JSON 
    following KnowledgeSchema.
    """
    
    def __init__(self, api_keys: Optional[Dict[str, str]] = None):
        """
        Initialize KnowledgeAgent with API keys and ADK tools.
        
        Args:
            api_keys: Dictionary with API keys for external services
                     Expected keys: 'weather_api_key', 'search_api_key', 'google_api_key'
        """
        self.system_prompt = """You are KnowledgeAgent. Use tools (Google Search or API) to return structured insight JSON following KnowledgeSchema. Summaries must be <= 40 words."""
        self.api_keys = api_keys or {}
        
        # Initialize ADK tool registry
        self.tool_registry = get_tool_registry()
        
        # Initialize tools if not already done
        if not self.tool_registry.tools:
            config = {'api_keys': self.api_keys}
            self.tool_registry.initialize_default_tools(config)
        
        # Legacy API endpoints for backward compatibility
        self.weather_api_url = "https://api.openweathermap.org/data/2.5/weather"
        self.search_api_url = "https://www.googleapis.com/customsearch/v1"
    
    def fetch_insights(
        self, 
        queries: List[str], 
        location: Optional[str] = None,
        task_context: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """
        Main method to fetch external insights.
        
        Args:
            queries: List of queries to search for
            location: User location for weather/local info
            task_context: Context about tasks that need insights
            
        Returns:
            JSON string with list of KnowledgeInsight objects
        """
        insights = []
        
        for query in queries:
            insight = self._process_single_query(query, location, task_context)
            insights.append(insight)
        
        insights_data = []
        for insight in insights:
            insight_dict = insight.dict()
            insight_dict['retrieved_at'] = insight_dict['retrieved_at'].isoformat()
            insights_data.append(insight_dict)
        
        return json.dumps(insights_data, indent=2)
    
    def fetch_insights_with_tools(self, queries: List[str], location: Optional[str] = None) -> str:
        """
        Enhanced insight fetching using ADK tools.
        
        Args:
            queries: List of queries to search for
            location: User location for weather/local info
            
        Returns:
            JSON string with enhanced insights from ADK tools
        """
        enhanced_insights = []
        
        for query in queries:
            query_lower = query.lower()
            
            # Use appropriate ADK tool based on query type
            if any(word in query_lower for word in ['weather', 'rain', 'snow', 'temperature']):
                weather_tool = self.tool_registry.get_tool('weather_service')
                if weather_tool:
                    tool_input = ToolInput(
                        query="current weather",
                        parameters={'location': location or 'New York'}
                    )
                    result = weather_tool.execute(tool_input)
                    
                    if result.success and result.result:
                        weather_data = result.result.get('weather', {})
                        recommendations = result.result.get('scheduling_recommendations', [])
                        
                        insight = KnowledgeInsight(
                            query=query,
                            summary=f"{weather_data.get('condition', 'N/A')}, {weather_data.get('temperature', 'N/A')}°F",
                            source="ADK Weather Tool",
                            confidence="high",
                            suggested_schedule_impact="; ".join(recommendations[:2]) if recommendations else None,
                            retrieved_at=datetime.now()
                        )
                        enhanced_insights.append(insight.dict())
                        continue
            
            elif any(word in query_lower for word in ['search', 'research', 'information']):
                search_tool = self.tool_registry.get_tool('google_search')
                if search_tool:
                    tool_input = ToolInput(
                        query=query,
                        parameters={'num_results': 3}
                    )
                    result = search_tool.execute(tool_input)
                    
                    if result.success and result.result:
                        search_results = result.result
                        if search_results:
                            summary = search_results[0].get('snippet', '')[:40] + "..." if search_results[0].get('snippet') else "Search results available"
                            
                            insight = KnowledgeInsight(
                                query=query,
                                summary=summary,
                                source="ADK Search Tool",
                                confidence="high",
                                suggested_schedule_impact=None,
                                retrieved_at=datetime.now()
                            )
                            enhanced_insights.append(insight.dict())
                            continue
            
            # Fallback to original processing
            original_insight = self._process_single_query(query, location)
            enhanced_insights.append(original_insight.dict())
        
        # Convert datetime objects for JSON serialization
        for insight in enhanced_insights:
            if 'retrieved_at' in insight:
                insight['retrieved_at'] = insight['retrieved_at'].isoformat() if hasattr(insight['retrieved_at'], 'isoformat') else insight['retrieved_at']
        
        return json.dumps(enhanced_insights, indent=2)
    
    def _process_single_query(
        self, 
        query: str, 
        location: Optional[str] = None, 
        task_context: Optional[List[Dict[str, Any]]] = None
    ) -> KnowledgeInsight:
        """
        Process a single knowledge query.
        
        Args:
            query: The query string
            location: User location
            task_context: Task context for relevance
            
        Returns:
            KnowledgeInsight object
        """
        query_lower = query.lower()
        
        # Determine query type and route to appropriate handler
        if any(word in query_lower for word in ['weather', 'rain', 'snow', 'temperature', 'forecast']):
            return self._fetch_weather_insight(query, location)
        elif any(word in query_lower for word in ['traffic', 'travel', 'commute', 'drive']):
            return self._fetch_travel_insight(query, location)
        elif any(word in query_lower for word in ['research', 'study', 'productivity', 'focus', 'timing']):
            return self._fetch_research_insight(query)
        else:
            return self._fetch_general_insight(query)
    
    def _fetch_weather_insight(self, query: str, location: Optional[str] = None) -> KnowledgeInsight:
        """
        Fetch weather information.
        
        Args:
            query: Weather-related query
            location: Location for weather data
            
        Returns:
            KnowledgeInsight with weather information
        """
        try:
            if not location:
                location = "New York"  # Default location
            
            # Mock weather data (in real implementation, use actual API)
            weather_data = self._get_mock_weather_data(location)
            
            if weather_data:
                summary = f"{weather_data['condition']}, {weather_data['temp']}°F, {weather_data['humidity']}% humidity"
                
                # Generate schedule impact based on weather
                impact = None
                if 'rain' in weather_data['condition'].lower():
                    impact = "Avoid outdoor activities 2-4pm due to rain"
                elif weather_data['temp'] > 85:
                    impact = "Schedule outdoor tasks before 11am due to high temperature"
                elif weather_data['temp'] < 32:
                    impact = "Allow extra travel time due to cold weather"
                
                return KnowledgeInsight(
                    query=query,
                    summary=summary,
                    source="Weather API",
                    confidence="high",
                    suggested_schedule_impact=impact,
                    retrieved_at=datetime.now()
                )
            else:
                raise Exception("No weather data available")
                
        except Exception as e:
            return KnowledgeInsight(
                query=query,
                summary=None,
                source=None,
                confidence="low",
                suggested_schedule_impact=None,
                retrieved_at=datetime.now()
            )
    
    def _fetch_travel_insight(self, query: str, location: Optional[str] = None) -> KnowledgeInsight:
        """
        Fetch travel and traffic information.
        
        Args:
            query: Travel-related query
            location: Starting location
            
        Returns:
            KnowledgeInsight with travel information
        """
        try:
            # Mock traffic data (in real implementation, use actual API)
            traffic_data = self._get_mock_traffic_data(location or "New York")
            
            if traffic_data:
                summary = f"Traffic: {traffic_data['condition']}, avg delay {traffic_data['delay']} mins"
                
                impact = None
                if traffic_data['delay'] > 15:
                    impact = "Add 20+ minutes for travel during 7-9am and 5-7pm"
                elif traffic_data['delay'] > 5:
                    impact = "Add 10 minutes buffer for travel"
                
                return KnowledgeInsight(
                    query=query,
                    summary=summary,
                    source="Traffic API",
                    confidence="medium",
                    suggested_schedule_impact=impact,
                    retrieved_at=datetime.now()
                )
            else:
                raise Exception("No traffic data available")
                
        except Exception as e:
            return KnowledgeInsight(
                query=query,
                summary=None,
                source=None,
                confidence="low",
                suggested_schedule_impact=None,
                retrieved_at=datetime.now()
            )
    
    def _fetch_research_insight(self, query: str) -> KnowledgeInsight:
        """
        Fetch research-backed productivity insights.
        
        Args:
            query: Research-related query
            
        Returns:
            KnowledgeInsight with research information
        """
        try:
            # Mock research insights (in real implementation, search academic sources)
            research_insights = {
                "focus": {
                    "summary": "Peak focus occurs 2-4 hours after waking, creativity peaks in late morning",
                    "impact": "Schedule analytical tasks 9-11am, creative work 11am-1pm"
                },
                "productivity": {
                    "summary": "90-minute focus blocks align with ultradian rhythms for optimal performance",
                    "impact": "Use 90-minute work blocks with 15-20 minute breaks"
                },
                "timing": {
                    "summary": "Most people have energy peaks at 10am, 2pm, and 6pm daily",
                    "impact": "Schedule important tasks at 10am or 2pm for best results"
                }
            }
            
            query_lower = query.lower()
            insight_key = None
            
            for key in research_insights.keys():
                if key in query_lower:
                    insight_key = key
                    break
            
            if insight_key:
                data = research_insights[insight_key]
                return KnowledgeInsight(
                    query=query,
                    summary=data['summary'],
                    source="Productivity Research",
                    confidence="high",
                    suggested_schedule_impact=data['impact'],
                    retrieved_at=datetime.now()
                )
            else:
                # Default productivity insight
                return KnowledgeInsight(
                    query=query,
                    summary="Regular breaks and time-blocking improve productivity by 25%",
                    source="Productivity Research",
                    confidence="medium",
                    suggested_schedule_impact="Use time-blocking and schedule breaks every 90 minutes",
                    retrieved_at=datetime.now()
                )
                
        except Exception as e:
            return KnowledgeInsight(
                query=query,
                summary=None,
                source=None,
                confidence="low",
                suggested_schedule_impact=None,
                retrieved_at=datetime.now()
            )
    
    def _fetch_general_insight(self, query: str) -> KnowledgeInsight:
        """
        Fetch general information using search.
        
        Args:
            query: General query
            
        Returns:
            KnowledgeInsight with general information
        """
        try:
            # Mock search results (in real implementation, use actual search API)
            summary = f"General information about {query} - consult relevant sources for details"
            
            return KnowledgeInsight(
                query=query,
                summary=summary,
                source="Search Results",
                confidence="medium",
                suggested_schedule_impact=None,
                retrieved_at=datetime.now()
            )
            
        except Exception as e:
            return KnowledgeInsight(
                query=query,
                summary=None,
                source=None,
                confidence="low",
                suggested_schedule_impact=None,
                retrieved_at=datetime.now()
            )
    
    def _get_mock_weather_data(self, location: str) -> Dict[str, Any]:
        """
        Generate mock weather data for demonstration.
        In real implementation, this would call actual weather API.
        """
        import random
        
        conditions = ["Sunny", "Partly Cloudy", "Cloudy", "Light Rain", "Heavy Rain", "Snow"]
        
        return {
            "condition": random.choice(conditions),
            "temp": random.randint(20, 85),
            "humidity": random.randint(30, 90),
            "location": location
        }
    
    def _get_mock_traffic_data(self, location: str) -> Dict[str, Any]:
        """
        Generate mock traffic data for demonstration.
        In real implementation, this would call actual traffic API.
        """
        import random
        
        conditions = ["Light", "Moderate", "Heavy", "Very Heavy"]
        
        return {
            "condition": random.choice(conditions),
            "delay": random.randint(0, 25),
            "location": location
        }
    
    def get_weather_for_tasks(
        self, 
        tasks: List[Dict[str, Any]], 
        location: Optional[str] = None
    ) -> str:
        """
        Get weather insights specifically for outdoor tasks.
        
        Args:
            tasks: List of tasks to check
            location: User location
            
        Returns:
            JSON string with weather insights
        """
        outdoor_tasks = [
            task for task in tasks 
            if any(tag in task.get('tags', []) for tag in ['outdoor', 'travel', 'commute'])
        ]
        
        if not outdoor_tasks:
            return json.dumps([], indent=2)
        
        return self.fetch_insights(["weather forecast for outdoor activities"], location, outdoor_tasks)
    
    def get_productivity_insights(
        self, 
        task_types: List[str]
    ) -> str:
        """
        Get research-backed productivity insights for specific task types.
        
        Args:
            task_types: Types of tasks (e.g., ['creative', 'analytical', 'routine'])
            
        Returns:
            JSON string with productivity insights
        """
        queries = [f"best timing for {task_type} tasks" for task_type in task_types]
        return self.fetch_insights(queries)
    
    def get_tool_usage_statistics(self) -> Dict[str, Any]:
        """
        Get usage statistics for all ADK tools.
        
        Returns:
            Dictionary with tool usage statistics
        """
        return self.tool_registry.get_usage_statistics()
    
    def list_available_tools(self) -> List[str]:
        """
        List all available ADK tools.
        
        Returns:
            List of available tool names
        """
        return self.tool_registry.list_tools()
    
    def execute_tool_directly(self, tool_name: str, query: str, parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute a specific ADK tool directly.
        
        Args:
            tool_name: Name of the tool to execute
            query: Query string for the tool
            parameters: Additional parameters
            
        Returns:
            Tool execution result
        """
        tool_input = ToolInput(
            query=query,
            parameters=parameters or {}
        )
        
        result = self.tool_registry.execute_tool(tool_name, tool_input)
        
        # Convert to dictionary for easier handling
        return {
            'result': result.result,
            'success': result.success,
            'error_message': result.error_message,
            'metadata': result.metadata,
            'timestamp': result.timestamp.isoformat()
        }