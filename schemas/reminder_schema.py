"""
Reminder Schema for the Smart Daily Productivity Assistant
Defines the structure for alerts and reminders.
"""

from typing import List, Literal
from pydantic import BaseModel, Field
from datetime import datetime

class Alert(BaseModel):
    """Individual alert for upcoming tasks."""
    alert_id: str = Field(..., description="Unique identifier for the alert")
    task_id: str = Field(..., description="ID of the associated task")
    task_title: str = Field(..., description="Title of the task")
    start_time: datetime = Field(..., description="When the task is scheduled to start")
    minutes_until_start: int = Field(..., description="Minutes until task starts (0 or positive)")
    actions: List[Literal["snooze 10", "reschedule 30", "mark_done"]] = Field(
        default_factory=list, description="Available actions for this alert"
    )
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class OverdueTask(BaseModel):
    """Task that is overdue."""
    task_id: str = Field(..., description="ID of the overdue task")
    task_title: str = Field(..., description="Title of the task")
    due_date: datetime = Field(..., description="Original due date")
    reason: str = Field(..., description="Reason why it's overdue")
    recommendation: str = Field(..., description="Suggested action for the overdue task")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class ReminderMeta(BaseModel):
    """Metadata for reminder check."""
    tick_time: datetime = Field(..., description="Time when reminder check was performed")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class ReminderResponse(BaseModel):
    """Complete reminder system response."""
    alerts: List[Alert] = Field(default_factory=list, description="Active alerts")
    overdue: List[OverdueTask] = Field(default_factory=list, description="Overdue tasks")
    meta: ReminderMeta = Field(..., description="Metadata about the reminder check")