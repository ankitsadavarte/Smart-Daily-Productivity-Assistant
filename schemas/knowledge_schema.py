"""
Knowledge Schema for the Smart Daily Productivity Assistant
Defines the structure for external knowledge and insights.
"""

from typing import Optional, Literal
from pydantic import BaseModel, Field
from datetime import datetime

class KnowledgeInsight(BaseModel):
    """External knowledge insight structure."""
    query: str = Field(..., description="The original query")
    summary: Optional[str] = Field(None, description="Summary of findings (≤40 words)")
    source: Optional[str] = Field(None, description="Source of the information")
    confidence: Literal["high", "medium", "low"] = Field(..., description="Confidence in the information")
    suggested_schedule_impact: Optional[str] = Field(None, description="Impact on scheduling")
    retrieved_at: datetime = Field(..., description="When the information was retrieved")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }