"""
Smart Daily Productivity Assistant - Main Entry Point
"""

from orchestrator import OrchestratorAgent
from config.settings import get_config
from utils.helpers import SessionManager
import sys
import json

def main():
    """Main function to run the productivity assistant."""
    print("🚀 Smart Daily Productivity Assistant")
    print("=" * 50)
    
    # Load configuration
    config = get_config()
    
    # Initialize session manager
    session_manager = SessionManager()
    
    # Initialize orchestrator
    orchestrator = OrchestratorAgent(config['api_keys'])
    
    # Try to load existing session
    existing_session = session_manager.load_session()
    if existing_session:
        orchestrator.set_session_state(existing_session)
        print("📂 Loaded existing session")
    else:
        print("🆕 Starting new session")
    
    # Main interaction loop
    print("\\nType 'help' for commands or 'quit' to exit")
    print("Examples:")
    print("- 'Add task: Review project proposal by tomorrow'")
    print("- 'Plan my day'")
    print("- 'Check reminders'")
    print("- 'Set work hours 9am to 6pm'")
    print()
    
    while True:
        try:
            user_input = input("💬 You: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'bye']:
                # Save session before exit
                session_manager.save_session(orchestrator.get_session_state())
                print("💾 Session saved. Goodbye! 👋")
                break
            
            elif user_input.lower() == 'help':
                show_help()
                continue
            
            elif user_input.lower() == 'status':
                show_status(orchestrator)
                continue
            
            elif user_input.lower().startswith('save'):
                session_id = user_input.split()[-1] if len(user_input.split()) > 1 else "default"
                success = session_manager.save_session(orchestrator.get_session_state(), session_id)
                if success:
                    print(f"✅ Session saved as '{session_id}'")
                else:
                    print("❌ Failed to save session")
                continue
            
            elif user_input.lower().startswith('load'):
                session_id = user_input.split()[-1] if len(user_input.split()) > 1 else "default"
                session_data = session_manager.load_session(session_id)
                if session_data:
                    orchestrator.set_session_state(session_data)
                    print(f"✅ Session '{session_id}' loaded")
                else:
                    print(f"❌ Session '{session_id}' not found")
                continue
            
            elif user_input.lower() == 'json':
                # Toggle machine mode for next input
                next_input = input("💬 JSON Mode - You: ").strip()
                response = orchestrator.process_user_request(next_input, machine_mode=True)
                print("🤖 JSON Response:")
                print(response)
                continue
            
            elif not user_input:
                continue
            
            # Process user request
            response = orchestrator.process_user_request(user_input)
            print(f"🤖 Assistant: {response}")
            print()
            
        except KeyboardInterrupt:
            # Save session before exit
            session_manager.save_session(orchestrator.get_session_state())
            print("\\n💾 Session saved. Goodbye! 👋")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            continue

def show_help():
    """Show available commands."""
    help_text = """
📚 Available Commands:

📝 Task Management:
   • "Add task: [description]" - Create new tasks
   • "Mark [task] done" - Complete tasks
   • "Update task [details]" - Modify existing tasks

📅 Planning:
   • "Plan my day" - Generate daily schedule
   • "Plan tomorrow" - Schedule for tomorrow
   • "Schedule tasks" - Organize current tasks

⏰ Reminders:
   • "Check reminders" - See upcoming alerts
   • "What's due?" - Check deadlines
   • "Show alerts" - Display active notifications

⚙️ Settings:
   • "Set work hours [time]" - Configure work schedule
   • "Set timezone [tz]" - Update timezone
   • "Set focus time [minutes]" - Change focus block duration

💾 Session Management:
   • "save [name]" - Save current session
   • "load [name]" - Load saved session
   • "status" - Show current session info

🔧 Other:
   • "json" - Next response in pure JSON format
   • "help" - Show this help
   • "quit" - Exit and save session

💡 Natural Language Examples:
   • "I need to call the dentist by Friday"
   • "Add a 2-hour meeting prep task for tomorrow"
   • "Plan my day with focus on creative work"
   • "What do I have coming up today?"
"""
    print(help_text)

def show_status(orchestrator: OrchestratorAgent):
    """Show current session status."""
    session_state = orchestrator.get_session_state()
    
    task_count = len(session_state['tasks'])
    completed_count = len(session_state['completed'])
    schedule_count = len(session_state['schedules'])
    
    print(f"""
📊 Session Status:
   📝 Tasks: {task_count} total, {completed_count} completed
   📅 Schedules: {schedule_count} created
   ⏰ Timezone: {session_state['preferences']['timezone']}
   🕘 Work Hours: {session_state['preferences']['work_hours']['start']} - {session_state['preferences']['work_hours']['end']}
   ⏱️ Focus Time: {session_state['preferences']['preferred_focus_minutes']} minutes
   📍 Location: {session_state['preferences'].get('location', 'Not set')}
   🔄 Last Updated: {session_state['last_updated']}
""")

if __name__ == "__main__":
    main()