# Smart Daily Productivity Assistant

A multi-agent system that helps you manage tasks, plan your day, and stay productive using natural language processing and intelligent scheduling.

## 🌟 Features

- **Natural Language Task Creation**: Convert spoken/written requests into structured tasks
- **Intelligent Daily Planning**: Generate conflict-free schedules with focus blocks
- **Proactive Reminders**: Get timely alerts for upcoming and overdue tasks
- **Contextual Insights**: Weather, traffic, and research-backed scheduling recommendations
- **Session Management**: Persistent state across sessions with auto-save
- **Multi-Agent Architecture**: Specialized agents working together seamlessly

## 🏗️ Architecture

The system uses a multi-agent architecture with specialized components:

### Core Agents
- **OrchestratorAgent**: Central coordinator managing all interactions
- **TaskCollector**: Converts natural language to structured task JSON  
- **SchedulePlanner**: Generates daily schedules with focus blocks and breaks
- **ReminderAgent**: Manages alerts and overdue task notifications
- **KnowledgeAgent**: Fetches external insights (weather, research, traffic)

### Data Schemas
- **TaskSchema**: Structured task representation with priority, duration, tags
- **ScheduleSchema**: Daily schedule with time blocks and unscheduled items
- **ReminderSchema**: Alert system with actions and overdue tracking
- **KnowledgeSchema**: External insights with confidence ratings

## 🚀 Quick Start

### Installation

```bash
# Clone or extract the project
cd Capstone_project

# Install dependencies
pip install -r requirements.txt
```

### Basic Usage

```bash
# Interactive mode
python main.py

# Run demo
python examples/demo.py

# Run tests
python -m pytest tests/
```

### Example Interactions

```
💬 You: I need to call the dentist by Friday and prepare for the team meeting tomorrow
🤖 Assistant: Added 2 task(s) to your list.

💬 You: Plan my day
🤖 Assistant: Created schedule for 2025-11-27 with 4 time blocks. 0 tasks couldn't be scheduled.

💬 You: Check reminders
🤖 Assistant: You have 2 upcoming task(s) and 0 overdue task(s).
```

## 📖 API Documentation

### OrchestratorAgent

Main entry point for all interactions:

```python
from orchestrator import OrchestratorAgent

# Initialize
orchestrator = OrchestratorAgent()

# Process requests
response = orchestrator.process_user_request("Add task: Review documents")

# Get JSON response
json_response = orchestrator.process_user_request("Plan my day", machine_mode=True)
```

### Task Creation

The system accepts natural language and extracts:
- Title and description
- Priority (low/medium/high)
- Due dates ("by Friday", "tomorrow", "next week")
- Duration ("2 hours", "30 minutes")
- Tags (automatically inferred)
- Recurring patterns ("daily", "weekly")

```python
# Examples of supported formats
"I need to call the dentist by Friday"
"URGENT: Fix server issues for 2 hours"  
"Daily standup meeting at 9am for 30 minutes"
"Review project proposal and send feedback"
```

### Schedule Planning

Generates optimized daily schedules:

```python
# Plan today
orchestrator.process_user_request("Plan my day")

# Plan specific date
orchestrator.process_user_request("Plan tomorrow")

# Features:
# - Respects work hours and blocked times
# - Splits long tasks into focus blocks
# - Adds breaks between sessions
# - Prioritizes by due date and importance
# - Integrates weather/traffic insights
```

### Reminders & Alerts

Proactive notification system:

```python
# Check current reminders
orchestrator.process_user_request("Check reminders")

# Available actions:
# - "snooze 10" - Delay alert by 10 minutes
# - "reschedule 30" - Move task 30 minutes later  
# - "mark_done" - Complete the task
```

## 🛠️ Agent Development Kit (ADK) Integration

### Enhanced Tool Capabilities

The project now includes a comprehensive Agent Development Kit (ADK) that provides standardized tools for all agents:

#### Available ADK Tools

- **SearchTool**: Google Custom Search integration with your API key
- **WeatherTool**: Advanced weather data and scheduling recommendations  
- **CalendarTool**: Calendar management with conflict detection
- **BaseTool**: Standardized interface for creating new tools

#### Using ADK Tools

```python
from tools.tool_registry import get_tool_registry
from tools.base_tool import ToolInput

# Get tool registry
tool_registry = get_tool_registry()

# Execute weather tool
weather_tool = tool_registry.get_tool('weather_service')
result = weather_tool.execute(ToolInput(
    query="current weather",
    parameters={'location': 'New York'}
))

# Execute search tool with your API key
search_tool = tool_registry.get_tool('google_search') 
result = search_tool.execute(ToolInput(
    query="productivity tips for morning work",
    parameters={'num_results': 5}
))
```

#### ADK Demo

```bash
# Run ADK integration demo
python examples/adk_demo.py
```

## 🛠️ Configuration

### Environment Variables

```bash
# Optional API keys for enhanced features
export WEATHER_API_KEY="your_openweathermap_key"
export GOOGLE_API_KEY=""
```

### Preferences

```python
# Set work hours
"Set work hours from 8am to 6pm"

# Configure focus time
"Set focus time to 120 minutes"

# Update timezone  
"Set timezone to America/New_York"
```

## 🔧 Integration Examples

### Web Application

```python
from examples.api_examples import ProductivityAPI

api = ProductivityAPI()

# Add tasks from web form
result = api.add_task(form_data['task_description'])

# Get schedule for dashboard
schedule = api.plan_day()

# Check for notifications
alerts = api.get_reminders()
```

### Slack Bot

```python
# Handle slash commands
if command.startswith("/task"):
    text = command.replace("/task ", "")
    result = api.add_task(text)
    return f"Task '{result['tasks'][0]['title']}' added!"

elif command.startswith("/schedule"):
    result = api.plan_day()  
    return f"Created schedule with {len(result['blocks'])} blocks!"
```

### Mobile App

```python
# Voice-to-text task creation
voice_input = "Remind me to pick up groceries"
api.add_task(voice_input)

# Widget integration
today_schedule = api.plan_day()
display_blocks = today_schedule['blocks'][:5]  # Show next 5 tasks
```

## 🧪 Testing

Run the test suite:

```bash
# All tests
python -m pytest tests/ -v

# Specific component
python -m pytest tests/test_task_collector.py -v

# With coverage
python -m pytest tests/ --cov=agents --cov-report=html
```

Test categories:
- **Unit Tests**: Individual agent functionality
- **Integration Tests**: Multi-agent workflows  
- **API Tests**: External interface validation

## 📁 Project Structure

```
Capstone_project/
├── agents/                 # Core AI agents
│   ├── task_collector.py   # NL to JSON conversion
│   ├── schedule_planner.py # Daily scheduling
│   ├── reminder_agent.py   # Alert management
│   └── knowledge_agent.py  # External insights (ADK-enhanced)
├── tools/                  # Agent Development Kit (ADK)
│   ├── base_tool.py        # Base tool interface
│   ├── search_tool.py      # Google Search integration
│   ├── weather_tool.py     # Weather data and recommendations
│   ├── calendar_tool.py    # Calendar management
│   └── tool_registry.py    # Tool coordination and management
├── schemas/                # Data structures
│   ├── task_schema.py      # Task definitions
│   ├── schedule_schema.py  # Schedule format
│   ├── reminder_schema.py  # Alert format
│   └── knowledge_schema.py # Insight format
├── utils/                  # Helper functions
│   └── helpers.py          # Session, time, validation utils
├── config/                 # Configuration
│   └── settings.py         # Default settings (with your API key)
├── tests/                  # Unit tests
│   ├── test_task_collector.py
│   └── test_schedule_planner.py
├── examples/               # Usage examples
│   ├── demo.py            # Interactive demo
│   ├── api_examples.py    # Integration examples
│   └── adk_demo.py        # ADK tools demonstration
├── orchestrator.py         # Main coordinator (ADK-integrated)
├── main.py                # Interactive CLI
├── requirements.txt       # Dependencies
└── README.md              # This file
```

## 🎯 Core Concepts

### Multi-Agent Orchestration

Each agent has a specific responsibility:
1. **TaskCollector** extracts structured data from natural language
2. **SchedulePlanner** creates optimal time-based schedules  
3. **ReminderAgent** handles time-sensitive notifications
4. **KnowledgeAgent** provides contextual external information
5. **OrchestratorAgent** coordinates everything and manages state

### Session State Management

Persistent memory across interactions:
```python
{
  "tasks": [...],           # All created tasks
  "completed": [...],       # Completion records  
  "blocked_times": [...],   # Unavailable time slots
  "preferences": {...},     # User settings
  "schedules": [...],       # Generated schedules
  "last_updated": "..."     # Timestamp
}
```

### JSON-First Design

All agents communicate via structured JSON:
- Enables reliable integration
- Supports both human and machine interfaces
- Facilitates testing and debugging
- Allows for easy API exposure

## 🔮 Advanced Features

### Knowledge Integration

- **Weather**: Avoid outdoor tasks during rain/extreme temperatures
- **Traffic**: Add buffer time during rush hours  
- **Research**: Schedule analytical work during peak focus hours
- **Productivity**: Optimize task timing based on circadian rhythms

### Intelligent Scheduling

- **Focus Blocks**: Split long tasks into manageable chunks (default 90min)
- **Break Management**: Automatic breaks between intensive sessions
- **Priority Weighting**: High-priority and due-soon tasks scheduled first
- **Conflict Resolution**: Handles overlapping demands gracefully
- **Context Awareness**: Weather/traffic impacts scheduling decisions

### Robust Error Handling

- **Retry Logic**: Failed operations retry once automatically
- **Graceful Degradation**: System works with partial data
- **Validation**: Input data validated against schemas
- **Fallback Responses**: Always provides useful output

## 🤝 Contributing

The system is designed for extensibility:

1. **New Agents**: Add specialized functionality (EmailAgent, CalendarAgent, etc.)
2. **Enhanced NLP**: Improve natural language understanding
3. **Additional APIs**: Integrate more external data sources
4. **UI Interfaces**: Web, mobile, or desktop frontends
5. **Workflow Automations**: Zapier, IFTTT, etc. integrations

## 📄 License

This project is provided as-is for educational and development purposes.

## 🙋‍♀️ Support

For questions or issues:
1. Check the examples in `examples/`
2. Run the demo: `python examples/demo.py`
3. Review test cases in `tests/`
4. Examine the source code - it's well-documented!

---

**Built with ❤️ using Python and multi-agent AI architecture**
