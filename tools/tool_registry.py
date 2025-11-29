"""
Tool Registry for Agent Development Kit.
Manages and coordinates all available tools for multi-agent system.
"""

from typing import Dict, Any, List, Optional, Type
from tools.base_tool import BaseTool, ToolInput, ToolOutput
from tools.search_tool import SearchTool
from tools.calendar_tool import CalendarTool
from tools.weather_tool import WeatherTool

class ToolRegistry:
    """
    Central registry for managing all ADK tools.
    Provides tool discovery, execution, and coordination.
    """
    
    def __init__(self):
        """Initialize tool registry."""
        self.tools: Dict[str, BaseTool] = {}
        self.tool_categories: Dict[str, List[str]] = {
            'knowledge': [],
            'scheduling': [],
            'communication': [],
            'utility': []
        }
    
    def register_tool(self, tool: BaseTool, category: str = 'utility') -> bool:
        """
        Register a new tool.
        
        Args:
            tool: Tool instance to register
            category: Tool category for organization
            
        Returns:
            True if registration successful
        """
        try:
            self.tools[tool.name] = tool
            
            if category not in self.tool_categories:
                self.tool_categories[category] = []
            
            self.tool_categories[category].append(tool.name)
            return True
        except Exception:
            return False
    
    def get_tool(self, tool_name: str) -> Optional[BaseTool]:
        """Get tool by name."""
        return self.tools.get(tool_name)
    
    def list_tools(self, category: Optional[str] = None) -> List[str]:
        """
        List available tools.
        
        Args:
            category: Filter by category (optional)
            
        Returns:
            List of tool names
        """
        if category:
            return self.tool_categories.get(category, [])
        else:
            return list(self.tools.keys())
    
    def execute_tool(self, tool_name: str, input_data: ToolInput) -> ToolOutput:
        """
        Execute a tool by name.
        
        Args:
            tool_name: Name of tool to execute
            input_data: Input data for tool
            
        Returns:
            Tool execution result
        """
        tool = self.get_tool(tool_name)
        if not tool:
            return ToolOutput(
                result=None,
                success=False,
                error_message=f"Tool '{tool_name}' not found"
            )
        
        return tool.execute(input_data)
    
    def get_tool_schemas(self) -> Dict[str, Dict[str, Any]]:
        """Get schemas for all registered tools."""
        schemas = {}
        for tool_name, tool in self.tools.items():
            schemas[tool_name] = tool.get_schema()
        return schemas
    
    def get_usage_statistics(self) -> Dict[str, Any]:
        """Get usage statistics for all tools."""
        stats = {}
        for tool_name, tool in self.tools.items():
            stats[tool_name] = tool.get_usage_stats()
        return stats
    
    def initialize_default_tools(self, config: Dict[str, Any]) -> None:
        """
        Initialize default tools with configuration.
        
        Args:
            config: Configuration dictionary with API keys and settings
        """
        api_keys = config.get('api_keys', {})
        
        # Initialize Search Tool
        google_api_key = api_keys.get('google_api_key')
        if google_api_key:
            search_tool = SearchTool(google_api_key)
            self.register_tool(search_tool, 'knowledge')
        
        # Initialize Calendar Tool
        calendar_tool = CalendarTool()
        self.register_tool(calendar_tool, 'scheduling')
        
        # Initialize Weather Tool
        weather_api_key = api_keys.get('weather_api_key')
        weather_tool = WeatherTool(weather_api_key)
        self.register_tool(weather_tool, 'knowledge')
    
    def find_tools_for_query(self, query: str) -> List[str]:
        """
        Find relevant tools for a given query.
        
        Args:
            query: User query or task description
            
        Returns:
            List of relevant tool names
        """
        query_lower = query.lower()
        relevant_tools = []
        
        # Knowledge-related keywords
        if any(word in query_lower for word in ['search', 'find', 'research', 'information', 'weather']):
            relevant_tools.extend(self.tool_categories.get('knowledge', []))
        
        # Scheduling-related keywords
        if any(word in query_lower for word in ['schedule', 'calendar', 'meeting', 'appointment', 'time']):
            relevant_tools.extend(self.tool_categories.get('scheduling', []))
        
        # Remove duplicates while preserving order
        return list(dict.fromkeys(relevant_tools))
    
    def batch_execute(self, operations: List[Dict[str, Any]]) -> List[ToolOutput]:
        """
        Execute multiple tool operations in batch.
        
        Args:
            operations: List of operations with tool_name and input_data
            
        Returns:
            List of execution results
        """
        results = []
        
        for operation in operations:
            tool_name = operation.get('tool_name')
            input_data = ToolInput(**operation.get('input_data', {}))
            
            if not tool_name:
                results.append(ToolOutput(
                    result=None,
                    success=False,
                    error_message="Tool name is required",
                    metadata={'operation': operation}
                ))
                continue
            
            result = self.execute_tool(tool_name, input_data)
            results.append(result)
        
        return results


# Global tool registry instance
tool_registry = ToolRegistry()


def get_tool_registry() -> ToolRegistry:
    """Get the global tool registry instance."""
    return tool_registry