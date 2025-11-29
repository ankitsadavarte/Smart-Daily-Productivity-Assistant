"""
Schedule Schema for the Smart Daily Productivity Assistant
Defines the structure for daily schedules and time blocks.
"""

from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

class ScheduleBlock(BaseModel):
    """Individual time block in a schedule."""
    start: datetime = Field(..., description="Start time as ISO datetime")
    end: datetime = Field(..., description="End time as ISO datetime")
    task_title: str = Field(..., description="Title of the task")
    task_id: str = Field(..., description="Unique identifier for the task")
    subtask_index: int = Field(1, description="Index if task is split into subtasks")
    notes: Optional[str] = Field(None, description="Additional notes for the block")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class UnscheduledTask(BaseModel):
    """Task that couldn't be scheduled."""
    task_title: str = Field(..., description="Title of the unscheduled task")
    reason: str = Field(..., description="Reason why it couldn't be scheduled")

class DailySchedule(BaseModel):
    """Complete daily schedule structure."""
    date: str = Field(..., description="Date of the schedule (YYYY-MM-DD)")
    time_zone: str = Field(..., description="Timezone for the schedule")
    blocks: List[ScheduleBlock] = Field(default_factory=list, description="List of scheduled blocks")
    unscheduled: List[UnscheduledTask] = Field(default_factory=list, description="Tasks that couldn't be scheduled")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }