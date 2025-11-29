"""
Task Schema for the Smart Daily Productivity Assistant
Defines the structure for tasks used throughout the system.
"""

from typing import Optional, List, Literal
from pydantic import BaseModel, Field
from datetime import datetime

class Task(BaseModel):
    """Task schema matching the specification."""
    title: str = Field(..., description="Title of the task")
    description: Optional[str] = Field(None, description="Detailed description")
    priority: Optional[Literal["low", "medium", "high"]] = Field(None, description="Task priority")
    due_date: Optional[datetime] = Field(None, description="ISO datetime string for due date")
    duration_minutes: Optional[int] = Field(None, description="Estimated duration in minutes")
    tags: List[str] = Field(default_factory=list, description="List of tags for categorization")
    recurring: Optional[Literal["daily", "weekly", "monthly"]] = Field(None, description="Recurring pattern")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class TaskList(BaseModel):
    """Container for multiple tasks."""
    tasks: List[Task]