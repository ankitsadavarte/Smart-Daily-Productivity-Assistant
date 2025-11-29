"""
Base Tool class for Agent Development Kit integration.
Provides standardized interface for all agent tools.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List
from pydantic import BaseModel, Field
from datetime import datetime

class ToolInput(BaseModel):
    """Base input schema for all tools."""
    query: str = Field(..., description="The input query or command")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional context data")
    parameters: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Tool-specific parameters")

class ToolOutput(BaseModel):
    """Base output schema for all tools."""
    result: Any = Field(..., description="Tool execution result")
    success: bool = Field(True, description="Whether tool executed successfully")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    timestamp: datetime = Field(default_factory=datetime.now, description="Execution timestamp")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class BaseTool(ABC):
    """
    Abstract base class for all ADK tools.
    Provides standardized interface for agent tool integration.
    """
    
    def __init__(self, name: str, description: str):
        """
        Initialize base tool.
        
        Args:
            name: Tool name identifier
            description: Human-readable tool description
        """
        self.name = name
        self.description = description
        self.usage_count = 0
        self.last_used = None
    
    @abstractmethod
    def execute(self, input_data: ToolInput) -> ToolOutput:
        """
        Execute the tool with given input.
        
        Args:
            input_data: Tool input data
            
        Returns:
            Tool execution result
        """
        pass
    
    def get_schema(self) -> Dict[str, Any]:
        """Get tool schema for agent integration."""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": ToolInput.schema(),
            "output_schema": ToolOutput.schema()
        }
    
    def _log_usage(self):
        """Log tool usage for analytics."""
        self.usage_count += 1
        self.last_used = datetime.now()
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get tool usage statistics."""
        return {
            "name": self.name,
            "usage_count": self.usage_count,
            "last_used": self.last_used.isoformat() if self.last_used else None
        }