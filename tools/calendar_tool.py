"""
Calendar Tool for Agent Development Kit.
Provides calendar integration capabilities for scheduling agents.
"""

from datetime import datetime, timedelta, date
from typing import Dict, Any, List, Optional
from tools.base_tool import BaseTool, ToolInput, ToolOutput

class CalendarTool(BaseTool):
    """
    Calendar management tool for scheduling operations.
    """
    
    def __init__(self):
        """Initialize calendar tool."""
        super().__init__(
            name="calendar_manager",
            description="Manage calendar events, check availability, and schedule conflicts"
        )
        self.events = []  # In-memory storage for demo
    
    def execute(self, input_data: ToolInput) -> ToolOutput:
        """
        Execute calendar operation based on query.
        
        Args:
            input_data: Calendar operation input
            
        Returns:
            Calendar operation result
        """
        self._log_usage()
        
        try:
            query = input_data.query.lower()
            
            if 'check availability' in query or 'free time' in query:
                return self._check_availability(input_data)
            elif 'add event' in query or 'schedule' in query:
                return self._add_event(input_data)
            elif 'conflicts' in query:
                return self._check_conflicts(input_data)
            elif 'list events' in query:
                return self._list_events(input_data)
            else:
                return ToolOutput(
                    result=[],
                    success=False,
                    error_message=f"Unknown calendar operation: {query}",
                    metadata={'operation': query}
                )
        except Exception as e:
            return ToolOutput(
                result=[],
                success=False,
                error_message=f"Calendar operation failed: {str(e)}",
                metadata={'operation': input_data.query, 'exception_type': type(e).__name__}
            )
    
    def _check_availability(self, input_data: ToolInput) -> ToolOutput:
        """Check availability for a given time period."""
        parameters = input_data.parameters or {}
        start_time = parameters.get('start_time')
        end_time = parameters.get('end_time')
        
        if not start_time or not end_time:
            # Default to checking today's availability
            today = date.today()
            start_time = datetime.combine(today, datetime.min.time().replace(hour=9))
            end_time = datetime.combine(today, datetime.min.time().replace(hour=17))
        else:
            start_time = datetime.fromisoformat(start_time)
            end_time = datetime.fromisoformat(end_time)
        
        # Check for conflicts
        conflicts = []
        for event in self.events:
            event_start = datetime.fromisoformat(event['start'])
            event_end = datetime.fromisoformat(event['end'])
            
            if (start_time < event_end and end_time > event_start):
                conflicts.append(event)
        
        # Find available time slots
        available_slots = []
        if not conflicts:
            available_slots.append({
                'start': start_time.isoformat(),
                'end': end_time.isoformat(),
                'duration_minutes': int((end_time - start_time).total_seconds() / 60)
            })
        
        return ToolOutput(
            result={
                'available_slots': available_slots,
                'conflicts': conflicts,
                'is_available': len(conflicts) == 0
            },
            success=True,
            error_message=None,
            metadata={
                'checked_period': {
                    'start': start_time.isoformat(),
                    'end': end_time.isoformat()
                }
            }
        )
    
    def _add_event(self, input_data: ToolInput) -> ToolOutput:
        """Add a new calendar event."""
        event_data = input_data.parameters or {}
        
        required_fields = ['title', 'start', 'end']
        for field in required_fields:
            if field not in event_data:
                return ToolOutput(
                    result=None,
                    success=False,
                    error_message=f"Missing required field: {field}",
                    metadata={'missing_field': field}
                )
        
        event = {
            'id': f"event_{len(self.events) + 1}",
            'title': event_data['title'],
            'start': event_data['start'],
            'end': event_data['end'],
            'description': event_data.get('description', ''),
            'created_at': datetime.now().isoformat()
        }
        
        self.events.append(event)
        
        return ToolOutput(
            result=event,
            success=True,
            error_message=None,
            metadata={'total_events': len(self.events)}
        )
    
    def _check_conflicts(self, input_data: ToolInput) -> ToolOutput:
        """Check for scheduling conflicts."""
        parameters = input_data.parameters or {}
        proposed_start = parameters.get('start')
        proposed_end = parameters.get('end')
        
        if not proposed_start or not proposed_end:
            return ToolOutput(
                result=[],
                success=False,
                error_message="Start and end times required for conflict checking",
                metadata={'required_fields': ['start', 'end']}
            )
        
        proposed_start = datetime.fromisoformat(proposed_start)
        proposed_end = datetime.fromisoformat(proposed_end)
        
        conflicts = []
        for event in self.events:
            event_start = datetime.fromisoformat(event['start'])
            event_end = datetime.fromisoformat(event['end'])
            
            if (proposed_start < event_end and proposed_end > event_start):
                conflicts.append(event)
        
        return ToolOutput(
            result=conflicts,
            success=True,
            error_message=None,
            metadata={
                'has_conflicts': len(conflicts) > 0,
                'conflict_count': len(conflicts)
            }
        )
    
    def _list_events(self, input_data: ToolInput) -> ToolOutput:
        """List calendar events."""
        parameters = input_data.parameters or {}
        date_filter = parameters.get('date')
        
        if date_filter:
            # Filter events by date
            target_date = datetime.fromisoformat(date_filter).date()
            filtered_events = []
            
            for event in self.events:
                event_date = datetime.fromisoformat(event['start']).date()
                if event_date == target_date:
                    filtered_events.append(event)
            
            return ToolOutput(
                result=filtered_events,
                success=True,
                error_message=None,
                metadata={'filtered_date': date_filter}
            )
        else:
            return ToolOutput(
                result=self.events,
                success=True,
                error_message=None,
                metadata={'total_events': len(self.events)}
            )
    
    def add_blocked_time(self, start: str, end: str, reason: str = "Blocked") -> ToolOutput:
        """
        Add blocked time to calendar.
        
        Args:
            start: Start time in ISO format
            end: End time in ISO format  
            reason: Reason for blocking time
            
        Returns:
            Block creation result
        """
        input_data = ToolInput(
            query="add event",
            parameters={
                'title': f"BLOCKED: {reason}",
                'start': start,
                'end': end,
                'description': f"Blocked time: {reason}"
            }
        )
        return self.execute(input_data)