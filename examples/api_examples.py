"""
API Usage Examples for Smart Daily Productivity Assistant.
Shows how to integrate the system into other applications.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
from typing import Optional
from orchestrator import OrchestratorAgent
from config.settings import get_config

class ProductivityAPI:
    """Wrapper API for easy integration."""
    
    def __init__(self, api_keys=None):
        """Initialize the API."""
        config = get_config()
        if api_keys:
            config['api_keys'].update(api_keys)
        
        self.orchestrator = OrchestratorAgent(config['api_keys'])
    
    def add_task(self, task_description: str) -> dict:
        """
        Add a new task.
        
        Args:
            task_description: Natural language task description
            
        Returns:
            Dictionary with task data and status
        """
        response = self.orchestrator.process_user_request(task_description, machine_mode=True)
        return json.loads(response)
    
    def plan_day(self, date: Optional[str] = None) -> dict:
        """
        Create a schedule for the specified date.
        
        Args:
            date: Date in YYYY-MM-DD format (defaults to today)
            
        Returns:
            Dictionary with schedule data
        """
        request = f"Plan my day for {date}" if date else "Plan my day"
        response = self.orchestrator.process_user_request(request, machine_mode=True)
        return json.loads(response)
    
    def get_reminders(self) -> dict:
        """
        Get current reminders and alerts.
        
        Returns:
            Dictionary with alerts and overdue tasks
        """
        response = self.orchestrator.process_user_request("Check reminders", machine_mode=True)
        return json.loads(response)
    
    def update_preferences(self, preferences: dict) -> dict:
        """
        Update user preferences.
        
        Args:
            preferences: Dictionary of preferences to update
            
        Returns:
            Updated preferences
        """
        # Convert preferences to natural language
        pref_text = self._preferences_to_text(preferences)
        response = self.orchestrator.process_user_request(pref_text, machine_mode=True)
        return json.loads(response)
    
    def get_session_state(self) -> dict:
        """Get current session state."""
        return self.orchestrator.get_session_state()
    
    def _preferences_to_text(self, preferences: dict) -> str:
        """Convert preferences dict to natural language."""
        text_parts = []
        
        if 'work_hours' in preferences:
            start = preferences['work_hours'].get('start')
            end = preferences['work_hours'].get('end')
            if start and end:
                text_parts.append(f"Set work hours from {start} to {end}")
        
        if 'preferred_focus_minutes' in preferences:
            minutes = preferences['preferred_focus_minutes']
            text_parts.append(f"Set focus time to {minutes} minutes")
        
        if 'timezone' in preferences:
            tz = preferences['timezone']
            text_parts.append(f"Set timezone to {tz}")
        
        return ". ".join(text_parts)

# Example usage functions

def example_web_app_integration():
    """Example: Integration with a web application."""
    print("🌐 Example: Web App Integration")
    print("=" * 40)
    
    # Initialize API
    api = ProductivityAPI()
    
    # Simulate web app requests
    print("1. User adds a task via web form:")
    task_result = api.add_task("Review marketing campaign materials for 90 minutes by Friday")
    print(f"   API Response: {json.dumps(task_result, indent=2)}\\n")
    
    print("2. User requests daily schedule:")
    schedule_result = api.plan_day()
    print(f"   API Response: {json.dumps(schedule_result, indent=2)}\\n")
    
    print("3. Check for notifications:")
    reminders_result = api.get_reminders()
    print(f"   API Response: {json.dumps(reminders_result, indent=2)}\\n")

def example_mobile_app_integration():
    """Example: Integration with a mobile application."""
    print("📱 Example: Mobile App Integration")
    print("=" * 40)
    
    api = ProductivityAPI()
    
    # Quick task addition (common mobile use case)
    print("1. Quick voice-to-text task addition:")
    voice_task = "Remind me to pick up groceries on the way home"
    result = api.add_task(voice_task)
    print(f"   Task created: {result.get('tasks', [{}])[0].get('title', 'N/A')}\\n")
    
    # Get today's schedule for widget
    print("2. Today widget schedule request:")
    today_schedule = api.plan_day()
    blocks = today_schedule.get('blocks', [])
    print(f"   Today's blocks: {len(blocks)} scheduled\\n")
    
    # Push notification check
    print("3. Push notification check:")
    alerts = api.get_reminders()
    alert_count = len(alerts.get('alerts', []))
    print(f"   Alerts to send: {alert_count}\\n")

def example_slack_bot_integration():
    """Example: Integration with Slack bot."""
    print("💬 Example: Slack Bot Integration")
    print("=" * 40)
    
    api = ProductivityAPI()
    
    # Simulate Slack commands
    slack_commands = [
        "/task Add code review for John's PR by EOD",
        "/schedule Plan my afternoon",
        "/reminders Show what's coming up"
    ]
    
    for i, command in enumerate(slack_commands, 1):
        print(f"{i}. Slack command: {command}")
        
        # Extract command and text
        if command.startswith("/task"):
            text = command.replace("/task ", "")
            result = api.add_task(text)
            print(f"   Bot response: Task '{result.get('tasks', [{}])[0].get('title', 'N/A')}' added!\\n")
        
        elif command.startswith("/schedule"):
            result = api.plan_day()
            block_count = len(result.get('blocks', []))
            print(f"   Bot response: Created schedule with {block_count} time blocks!\\n")
        
        elif command.startswith("/reminders"):
            result = api.get_reminders()
            alert_count = len(result.get('alerts', []))
            overdue_count = len(result.get('overdue', []))
            print(f"   Bot response: {alert_count} upcoming, {overdue_count} overdue tasks!\\n")

def example_calendar_integration():
    """Example: Integration with calendar systems."""
    print("📆 Example: Calendar Integration")
    print("=" * 40)
    
    api = ProductivityAPI()
    
    # Create tasks from calendar events
    print("1. Import calendar events as tasks:")
    calendar_events = [
        "Team standup meeting tomorrow 9am for 30 minutes",
        "Client presentation Friday 2pm for 2 hours",
        "Project deadline review next Monday"
    ]
    
    for event in calendar_events:
        result = api.add_task(f"Prepare for {event}")
        print(f"   Imported: {result.get('tasks', [{}])[0].get('title', 'N/A')}")
    
    print()
    
    # Export schedule to calendar format
    print("2. Export schedule for calendar sync:")
    schedule = api.plan_day()
    blocks = schedule.get('blocks', [])
    
    print("   Calendar entries to create:")
    for block in blocks[:3]:  # Show first 3
        start = block.get('start', 'N/A')
        title = block.get('task_title', 'N/A')
        print(f"   - {start}: {title}")
    
    print()

def main():
    """Run all API integration examples."""
    print("🔧 Smart Daily Productivity Assistant - API Examples")
    print("=" * 60)
    print("These examples show how to integrate the system into various applications.\\n")
    
    try:
        example_web_app_integration()
        example_mobile_app_integration()
        example_slack_bot_integration()
        example_calendar_integration()
        
        print("✅ All API examples completed successfully!")
        print("\\n💡 Integration Tips:")
        print("- Use machine_mode=True for JSON responses")
        print("- Handle errors gracefully in production")
        print("- Consider rate limiting for high-volume usage")
        print("- Cache session state for better performance")
        
    except Exception as e:
        print(f"❌ Error running examples: {e}")
        print("Make sure all dependencies are installed and configured properly.")

if __name__ == "__main__":
    main()