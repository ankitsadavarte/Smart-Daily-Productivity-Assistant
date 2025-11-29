"""
Search Tool for Agent Development Kit.
Provides Google Custom Search integration for knowledge agents.
"""

import requests
from typing import Dict, Any, List, Optional
from tools.base_tool import BaseTool, ToolInput, ToolOutput

class SearchTool(BaseTool):
    """
    Google Custom Search tool for agent knowledge retrieval.
    """
    
    def __init__(self, api_key: str, search_engine_id: Optional[str] = None):
        """
        Initialize search tool.
        
        Args:
            api_key: Google Custom Search API key
            search_engine_id: Custom Search Engine ID (optional)
        """
        super().__init__(
            name="google_search",
            description="Search Google for information and return structured results"
        )
        self.api_key = api_key
        self.search_engine_id = search_engine_id or "017576662512468239146:omuauf_lfve"
        self.base_url = "https://www.googleapis.com/customsearch/v1"
    
    def execute(self, input_data: ToolInput) -> ToolOutput:
        """
        Execute Google search query.
        
        Args:
            input_data: Search input containing query
            
        Returns:
            Search results with structured data
        """
        self._log_usage()
        
        try:
            query = input_data.query
            parameters = input_data.parameters or {}
            num_results = parameters.get('num_results', 5)
            
            # Prepare search parameters
            params = {
                'key': self.api_key,
                'cx': self.search_engine_id,
                'q': query,
                'num': min(num_results, 10)  # Google API limit
            }
            
            # Execute search request
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            # Extract search results
            results = []
            for item in data.get('items', []):
                results.append({
                    'title': item.get('title', ''),
                    'link': item.get('link', ''),
                    'snippet': item.get('snippet', ''),
                    'displayLink': item.get('displayLink', '')
                })
            
            return ToolOutput(
                result=results,
                success=True,
                error_message=None,
                metadata={
                    'query': query,
                    'total_results': data.get('searchInformation', {}).get('totalResults', '0'),
                    'search_time': data.get('searchInformation', {}).get('searchTime', '0')
                }
            )
            
        except requests.RequestException as e:
            return ToolOutput(
                result=[],
                success=False,
                error_message=f"Search request failed: {str(e)}",
                metadata={'query': input_data.query}
            )
        except Exception as e:
            return ToolOutput(
                result=[],
                success=False,
                error_message=f"Search execution failed: {str(e)}",
                metadata={'query': input_data.query}
            )
    
    def search_productivity_tips(self, task_type: str) -> ToolOutput:
        """
        Search for productivity tips for specific task types.
        
        Args:
            task_type: Type of task (e.g., 'creative', 'analytical')
            
        Returns:
            Productivity research results
        """
        input_data = ToolInput(
            query=f"productivity tips {task_type} tasks best time schedule",
            parameters={'num_results': 3}
        )
        return self.execute(input_data)
    
    def search_weather_impact(self, location: str, activity: str) -> ToolOutput:
        """
        Search for weather impact on specific activities.
        
        Args:
            location: Location for weather search
            activity: Type of activity
            
        Returns:
            Weather impact information
        """
        input_data = ToolInput(
            query=f"weather impact {activity} {location} best time outdoor",
            parameters={'num_results': 2}
        )
        return self.execute(input_data)