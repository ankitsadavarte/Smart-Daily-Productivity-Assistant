"""
Example usage of the Smart Daily Productivity Assistant.
Run this script to see the system in action with sample data.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from orchestrator import OrchestratorAgent
from config.settings import get_config
import json

def demo_task_creation():
    """Demonstrate task creation functionality."""
    print("🎯 Demo: Task Creation")
    print("=" * 30)
    
    # Initialize orchestrator
    config = get_config()
    orchestrator = OrchestratorAgent(config['api_keys'])
    
    # Sample task creation requests
    task_requests = [
        "I need to call the dentist by Friday",
        "Add task: Review project proposal for 2 hours tomorrow",
        "URGENT: Fix server issues and Email team about downtime",
        "Someday I should organize my digital photos",
        "Daily standup meeting at 9am for 30 minutes"
    ]
    
    print("Adding sample tasks...\\n")
    
    for request in task_requests:
        print(f"📝 Request: {request}")
        response = orchestrator.process_user_request(request)
        print(f"🤖 Response: {response}\\n")
    
    return orchestrator

def demo_day_planning(orchestrator):
    """Demonstrate day planning functionality."""
    print("📅 Demo: Day Planning")
    print("=" * 30)
    
    # Plan the day
    planning_request = "Plan my day for today"
    print(f"📝 Request: {planning_request}")
    response = orchestrator.process_user_request(planning_request)
    print(f"🤖 Response: {response}\\n")
    
    return orchestrator

def demo_reminders(orchestrator):
    """Demonstrate reminder checking functionality."""
    print("⏰ Demo: Reminder Checking")
    print("=" * 30)
    
    # Check reminders
    reminder_request = "Check my reminders"
    print(f"📝 Request: {reminder_request}")
    response = orchestrator.process_user_request(reminder_request)
    print(f"🤖 Response: {response}\\n")

def demo_preferences(orchestrator):
    """Demonstrate preference setting."""
    print("⚙️ Demo: Setting Preferences")
    print("=" * 30)
    
    # Set work hours
    pref_request = "Set my work hours from 8am to 6pm"
    print(f"📝 Request: {pref_request}")
    response = orchestrator.process_user_request(pref_request)
    print(f"🤖 Response: {response}\\n")
    
    # Set focus time
    focus_request = "Set focus time to 120 minutes"
    print(f"📝 Request: {focus_request}")
    response = orchestrator.process_user_request(focus_request)
    print(f"🤖 Response: {response}\\n")

def demo_machine_mode(orchestrator):
    """Demonstrate machine/JSON mode."""
    print("🤖 Demo: Machine Mode (Pure JSON)")
    print("=" * 30)
    
    # Get pure JSON response
    json_request = "What tasks do I have due soon?"
    print(f"📝 Request: {json_request}")
    response = orchestrator.process_user_request(json_request, machine_mode=True)
    print(f"🔧 JSON Response:\\n{response}\\n")

def demo_session_state(orchestrator):
    """Show current session state."""
    print("📊 Demo: Session State")
    print("=" * 30)
    
    session_state = orchestrator.get_session_state()
    
    print(f"📝 Total Tasks: {len(session_state['tasks'])}")
    print(f"✅ Completed Tasks: {len(session_state['completed'])}")
    print(f"📅 Schedules Created: {len(session_state['schedules'])}")
    print(f"⏰ Current Timezone: {session_state['preferences']['timezone']}")
    print(f"🕘 Work Hours: {session_state['preferences']['work_hours']['start']} - {session_state['preferences']['work_hours']['end']}")
    print(f"⏱️ Focus Time: {session_state['preferences']['preferred_focus_minutes']} minutes")
    print()

def main():
    """Run the complete demonstration."""
    print("🚀 Smart Daily Productivity Assistant - Demo")
    print("=" * 50)
    print("This demo shows all the key features of the system.\\n")
    
    # Run demonstrations
    orchestrator = demo_task_creation()
    orchestrator = demo_day_planning(orchestrator)
    demo_reminders(orchestrator)
    demo_preferences(orchestrator)
    demo_machine_mode(orchestrator)
    demo_session_state(orchestrator)
    
    print("✨ Demo completed! The system is ready for interactive use.")
    print("Run 'python main.py' to start the interactive mode.")

if __name__ == "__main__":
    main()