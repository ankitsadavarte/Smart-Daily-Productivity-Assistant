"""
Utility functions for the Smart Daily Productivity Assistant.
"""

import json
import pickle
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from pathlib import Path

class SessionManager:
    """Manages session persistence and state."""
    
    def __init__(self, session_dir: str = "sessions"):
        """
        Initialize SessionManager.
        
        Args:
            session_dir: Directory to store session files
        """
        self.session_dir = Path(session_dir)
        self.session_dir.mkdir(exist_ok=True)
    
    def save_session(self, session_state: Dict[str, Any], session_id: str = "default") -> bool:
        """
        Save session state to file.
        
        Args:
            session_state: Current session state
            session_id: Unique identifier for the session
            
        Returns:
            True if saved successfully
        """
        try:
            session_file = self.session_dir / f"{session_id}.json"
            
            # Add metadata
            session_with_meta = {
                "session_data": session_state,
                "saved_at": datetime.now().isoformat(),
                "version": "1.0"
            }
            
            with open(session_file, 'w') as f:
                json.dump(session_with_meta, f, indent=2)
            
            return True
        except Exception as e:
            print(f"Failed to save session: {e}")
            return False
    
    def load_session(self, session_id: str = "default") -> Optional[Dict[str, Any]]:
        """
        Load session state from file.
        
        Args:
            session_id: Unique identifier for the session
            
        Returns:
            Session state or None if not found
        """
        try:
            session_file = self.session_dir / f"{session_id}.json"
            
            if not session_file.exists():
                return None
            
            with open(session_file, 'r') as f:
                session_with_meta = json.load(f)
            
            return session_with_meta.get("session_data")
        except Exception as e:
            print(f"Failed to load session: {e}")
            return None
    
    def list_sessions(self) -> List[str]:
        """List all available session IDs."""
        session_files = self.session_dir.glob("*.json")
        return [f.stem for f in session_files]
    
    def cleanup_old_sessions(self, days: int = 30):
        """Remove session files older than specified days."""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        for session_file in self.session_dir.glob("*.json"):
            try:
                with open(session_file, 'r') as f:
                    session_data = json.load(f)
                
                saved_at = datetime.fromisoformat(session_data.get("saved_at", ""))
                if saved_at < cutoff_date:
                    session_file.unlink()
            except Exception:
                continue

class TimeUtils:
    """Utility functions for time and date operations."""
    
    @staticmethod
    def parse_natural_date(date_str: str) -> Optional[datetime]:
        """
        Parse natural language date strings.
        
        Args:
            date_str: Natural language date (e.g., "tomorrow", "next Monday")
            
        Returns:
            Parsed datetime or None
        """
        date_str_lower = date_str.lower().strip()
        now = datetime.now()
        
        if date_str_lower in ['today']:
            return now.replace(hour=9, minute=0, second=0, microsecond=0)
        elif date_str_lower in ['tomorrow']:
            return (now + timedelta(days=1)).replace(hour=9, minute=0, second=0, microsecond=0)
        elif date_str_lower in ['yesterday']:
            return (now - timedelta(days=1)).replace(hour=9, minute=0, second=0, microsecond=0)
        
        # Weekdays
        weekdays = {
            'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
            'friday': 4, 'saturday': 5, 'sunday': 6
        }
        
        for day_name, day_num in weekdays.items():
            if day_name in date_str_lower:
                days_ahead = day_num - now.weekday()
                if days_ahead <= 0:  # Target day already happened this week
                    days_ahead += 7
                
                if 'next' in date_str_lower:
                    days_ahead += 7
                
                target_date = now + timedelta(days=days_ahead)
                return target_date.replace(hour=9, minute=0, second=0, microsecond=0)
        
        return None
    
    @staticmethod
    def format_duration(minutes: int) -> str:
        """
        Format duration in minutes to human-readable string.
        
        Args:
            minutes: Duration in minutes
            
        Returns:
            Formatted duration string
        """
        if minutes < 60:
            return f"{minutes} minutes"
        elif minutes < 1440:  # Less than a day
            hours = minutes // 60
            mins = minutes % 60
            if mins == 0:
                return f"{hours} hour{'s' if hours != 1 else ''}"
            else:
                return f"{hours}h {mins}m"
        else:
            days = minutes // 1440
            remaining_minutes = minutes % 1440
            hours = remaining_minutes // 60
            return f"{days} day{'s' if days != 1 else ''} {hours}h"
    
    @staticmethod
    def is_work_hours(dt: datetime, work_start: str = "09:00", work_end: str = "17:00") -> bool:
        """
        Check if datetime falls within work hours.
        
        Args:
            dt: Datetime to check
            work_start: Work start time (HH:MM format)
            work_end: Work end time (HH:MM format)
            
        Returns:
            True if within work hours
        """
        work_start_time = datetime.strptime(work_start, "%H:%M").time()
        work_end_time = datetime.strptime(work_end, "%H:%M").time()
        
        return work_start_time <= dt.time() <= work_end_time

class ValidationUtils:
    """Utility functions for data validation."""
    
    @staticmethod
    def validate_task(task: Dict[str, Any]) -> List[str]:
        """
        Validate task data structure.
        
        Args:
            task: Task dictionary to validate
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Required fields
        if not task.get('title'):
            errors.append("Task title is required")
        
        # Priority validation
        valid_priorities = ['low', 'medium', 'high', None]
        if task.get('priority') not in valid_priorities:
            errors.append(f"Invalid priority: {task.get('priority')}")
        
        # Duration validation
        duration = task.get('duration_minutes')
        if duration is not None and (not isinstance(duration, int) or duration <= 0):
            errors.append("Duration must be a positive integer")
        
        # Due date validation
        due_date = task.get('due_date')
        if due_date is not None:
            try:
                datetime.fromisoformat(due_date.replace('Z', '+00:00'))
            except ValueError:
                errors.append("Invalid due date format")
        
        return errors
    
    @staticmethod
    def validate_schedule(schedule: Dict[str, Any]) -> List[str]:
        """
        Validate schedule data structure.
        
        Args:
            schedule: Schedule dictionary to validate
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Required fields
        required_fields = ['date', 'time_zone', 'blocks']
        for field in required_fields:
            if field not in schedule:
                errors.append(f"Missing required field: {field}")
        
        # Validate blocks
        blocks = schedule.get('blocks', [])
        for i, block in enumerate(blocks):
            block_errors = ValidationUtils.validate_schedule_block(block)
            for error in block_errors:
                errors.append(f"Block {i+1}: {error}")
        
        return errors
    
    @staticmethod
    def validate_schedule_block(block: Dict[str, Any]) -> List[str]:
        """
        Validate a single schedule block.
        
        Args:
            block: Schedule block dictionary
            
        Returns:
            List of validation errors
        """
        errors = []
        
        # Required fields
        required_fields = ['start', 'end', 'task_title', 'task_id']
        for field in required_fields:
            if field not in block:
                errors.append(f"Missing required field: {field}")
        
        # Time validation
        try:
            start_time = datetime.fromisoformat(block['start'])
            end_time = datetime.fromisoformat(block['end'])
            
            if start_time >= end_time:
                errors.append("Start time must be before end time")
        except (ValueError, KeyError):
            errors.append("Invalid time format")
        
        return errors

class FileUtils:
    """Utility functions for file operations."""
    
    @staticmethod
    def ensure_directory_exists(directory_path: str):
        """Ensure a directory exists, create if it doesn't."""
        Path(directory_path).mkdir(parents=True, exist_ok=True)
    
    @staticmethod
    def read_json_file(file_path: str) -> Optional[Dict[str, Any]]:
        """Read JSON file safely."""
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except Exception:
            return None
    
    @staticmethod
    def write_json_file(file_path: str, data: Dict[str, Any]) -> bool:
        """Write JSON file safely."""
        try:
            # Ensure directory exists
            FileUtils.ensure_directory_exists(os.path.dirname(file_path))
            
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
            return True
        except Exception:
            return False