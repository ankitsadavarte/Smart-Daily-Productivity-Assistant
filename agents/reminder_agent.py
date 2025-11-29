"""
ReminderAgent - Handles alerts and reminders for upcoming and overdue tasks.
This agent checks schedules and generates timely notifications.
"""

import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Literal
from schemas.reminder_schema import ReminderResponse, Alert, OverdueTask, ReminderMeta

class ReminderAgent:
    """
    ReminderAgent - Periodic (loop) or on-demand reminder engine.
    Checks schedule and tasks, outputs alerts as JSON using ReminderSchema.
    """
    
    def __init__(self):
        """Initialize ReminderAgent with system prompt behavior."""
        self.system_prompt = """You are ReminderAgent. Check schedule and tasks. Output alerts as JSON using the ReminderSchema. Only JSON."""
        self.alert_history = {}  # Track sent alerts to avoid duplicates
    
    def check_reminders(
        self, 
        schedule: Dict[str, Any], 
        tasks: List[Dict[str, Any]], 
        preferences: Optional[Dict[str, Any]] = None,
        current_time: Optional[datetime] = None
    ) -> str:
        """
        Main method to check for reminders and alerts.
        
        Args:
            schedule: Current schedule dictionary
            tasks: List of all tasks
            preferences: User preferences (alert_window_minutes, etc.)
            current_time: Current time (for testing, defaults to now)
            
        Returns:
            JSON string matching ReminderSchema
        """
        try:
            if current_time is None:
                current_time = datetime.now()
            
            if preferences is None:
                preferences = {"alert_window_minutes": 60}
            
            alert_window = preferences.get('alert_window_minutes', 60)
            
            # Check for upcoming tasks (alerts)
            alerts = self._check_upcoming_tasks(schedule, current_time, alert_window)
            
            # Check for overdue tasks
            overdue = self._check_overdue_tasks(tasks, current_time)
            
            # Create response
            response = ReminderResponse(
                alerts=alerts,
                overdue=overdue,
                meta=ReminderMeta(tick_time=current_time)
            )
            
            # Convert datetime objects manually for JSON serialization
            response_dict = response.dict()
            
            # Convert alert datetime objects
            for alert in response_dict.get('alerts', []):
                if isinstance(alert.get('start_time'), datetime):
                    alert['start_time'] = alert['start_time'].isoformat()
            
            # Convert overdue datetime objects
            for overdue in response_dict.get('overdue', []):
                if isinstance(overdue.get('due_date'), datetime):
                    overdue['due_date'] = overdue['due_date'].isoformat()
            
            # Convert meta datetime
            if isinstance(response_dict.get('meta', {}).get('tick_time'), datetime):
                response_dict['meta']['tick_time'] = response_dict['meta']['tick_time'].isoformat()
            
            return json.dumps(response_dict, indent=2)
            
        except Exception as e:
            # Fallback response
            fallback = {
                "alerts": [],
                "overdue": [],
                "meta": {
                    "tick_time": current_time.isoformat() if current_time else datetime.now().isoformat()
                }
            }
            return json.dumps(fallback, indent=2)
    
    def _check_upcoming_tasks(
        self, 
        schedule: Dict[str, Any], 
        current_time: datetime, 
        alert_window_minutes: int
    ) -> List[Alert]:
        """Check for tasks starting within the alert window."""
        alerts = []
        
        if not schedule or 'blocks' not in schedule:
            return alerts
        
        alert_cutoff = current_time + timedelta(minutes=alert_window_minutes)
        
        for block in schedule['blocks']:
            try:
                start_time = datetime.fromisoformat(block['start'])
                
                # Check if task starts within alert window
                if current_time <= start_time <= alert_cutoff:
                    minutes_until = int((start_time - current_time).total_seconds() // 60)
                    
                    # Generate unique alert ID
                    alert_id = f"{block['task_id']}-{start_time.strftime('%H%M')}"
                    
                    # Check if we've already alerted for this task (idempotent alerts)
                    if self._should_send_alert(alert_id, start_time):
                        alert = Alert(
                            alert_id=alert_id,
                            task_id=block['task_id'],
                            task_title=block['task_title'],
                            start_time=start_time,
                            minutes_until_start=minutes_until,
                            actions=self._get_available_actions(minutes_until)
                        )
                        
                        alerts.append(alert)
                        self._record_alert(alert_id, start_time)
            
            except (ValueError, KeyError) as e:
                # Skip malformed blocks
                continue
        
        return alerts
    
    def _check_overdue_tasks(
        self, 
        tasks: List[Dict[str, Any]], 
        current_time: datetime
    ) -> List[OverdueTask]:
        """Check for tasks that are past their due date."""
        overdue = []
        
        for task in tasks:
            due_date_str = task.get('due_date')
            if not due_date_str:
                continue
            
            try:
                due_date = datetime.fromisoformat(due_date_str.replace('Z', '+00:00'))
                
                if due_date < current_time:
                    # Task is overdue
                    days_overdue = (current_time - due_date).days
                    
                    overdue_task = OverdueTask(
                        task_id=self._generate_task_id(task),
                        task_title=task.get('title', 'Untitled Task'),
                        due_date=due_date,
                        reason=self._get_overdue_reason(days_overdue),
                        recommendation=self._get_overdue_recommendation(task, days_overdue)
                    )
                    
                    overdue.append(overdue_task)
            
            except (ValueError, TypeError):
                # Skip tasks with invalid due dates
                continue
        
        return overdue
    
    def _should_send_alert(self, alert_id: str, start_time: datetime) -> bool:
        """Check if we should send an alert (idempotent behavior)."""
        # Only alert once per task per window
        if alert_id in self.alert_history:
            last_alert_time = self.alert_history[alert_id]
            # Don't alert again within 30 minutes
            if (datetime.now() - last_alert_time).total_seconds() < 1800:
                return False
        
        return True
    
    def _record_alert(self, alert_id: str, start_time: datetime):
        """Record that we sent an alert for this task."""
        self.alert_history[alert_id] = datetime.now()
        
        # Clean up old alerts (older than 24 hours)
        cutoff = datetime.now() - timedelta(hours=24)
        self.alert_history = {
            k: v for k, v in self.alert_history.items() 
            if v > cutoff
        }
    

    
    def _generate_task_id(self, task: Dict[str, Any]) -> str:
        """Generate a task ID for tasks that don't have one."""
        title = task.get('title', 'task')
        # Create a slug from the title
        slug = title.lower().replace(' ', '-').replace('_', '-')
        slug = ''.join(c for c in slug if c.isalnum() or c == '-')[:20]
        return f"{slug}-{datetime.now().strftime('%Y%m%d')}"
    
    def _get_overdue_reason(self, days_overdue: int) -> str:
        """Generate a reason for why a task is overdue."""
        if days_overdue == 0:
            return "Due date was today"
        elif days_overdue == 1:
            return "Due date was yesterday"
        elif days_overdue <= 7:
            return f"Due date was {days_overdue} days ago"
        elif days_overdue <= 30:
            return f"Due date was {days_overdue // 7} weeks ago"
        else:
            return f"Due date was {days_overdue // 30} months ago"
    
    def _get_overdue_recommendation(self, task: Dict[str, Any], days_overdue: int) -> str:
        """Generate a recommendation for handling overdue tasks."""
        priority = task.get('priority', 'medium')
        
        if days_overdue <= 1:
            if priority == 'high':
                return "Reschedule immediately to today"
            else:
                return "Reschedule to tomorrow or mark as done if completed"
        elif days_overdue <= 7:
            if priority == 'high':
                return "Urgent: Reschedule to today or next available slot"
            elif priority == 'medium':
                return "Reschedule to this week or evaluate if still needed"
            else:
                return "Consider if this task is still relevant or can be cancelled"
        else:
            return "Evaluate if this task is still needed, consider marking as cancelled"
    
    def process_reminder_tick(
        self, 
        schedule: Dict[str, Any], 
        tasks: List[Dict[str, Any]], 
        preferences: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Process a reminder tick (periodic check).
        This is the main entry point following the system prompt.
        """
        return self.check_reminders(schedule, tasks, preferences)
    
    def _get_available_actions(self, minutes_until: int) -> List[Literal["snooze 10", "reschedule 30", "mark_done"]]:
        """Get available actions based on minutes until task start."""
        actions: List[Literal["snooze 10", "reschedule 30", "mark_done"]] = []
        
        if minutes_until > 10:
            actions.append("snooze 10")
        if minutes_until > 30:
            actions.append("reschedule 30")
        actions.append("mark_done")
        
        return actions