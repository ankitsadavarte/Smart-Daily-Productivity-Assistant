"""
OrchestratorAgent - Central coordinator of the Smart Daily Productivity Assistant.
Manages sub-agents, session state, and user interactions.
"""

import json
from datetime import datetime, date
from typing import List, Dict, Any, Optional, Union
from agents.task_collector import TaskCollector
from agents.schedule_planner import SchedulePlanner
from agents.reminder_agent import ReminderAgent
from agents.knowledge_agent import KnowledgeAgent
from tools.tool_registry import get_tool_registry

class OrchestratorAgent:
    """
    OrchestratorAgent - The central coordinator that interprets user requests,
    manages memory/session state, and calls appropriate sub-agents to produce
    final results that are actionable, correct, and easy for the user.
    """
    
    def __init__(self, api_keys: Optional[Dict[str, str]] = None):
        """
        Initialize the OrchestratorAgent with all sub-agents.
        
        Args:
            api_keys: Dictionary with API keys for external services
        """
        # Initialize sub-agents
        self.task_collector = TaskCollector()
        self.schedule_planner = SchedulePlanner()
        self.reminder_agent = ReminderAgent()
        self.knowledge_agent = KnowledgeAgent(api_keys)
        
        # Initialize session memory
        self.session_state = {
            "tasks": [],
            "completed": [],
            "blocked_times": [],
            "preferences": {
                "work_hours": {"start": "09:00", "end": "17:00"},
                "preferred_focus_minutes": 90,
                "alert_window_minutes": 60,
                "timezone": "UTC"
            },
            "schedules": [],
            "last_updated": datetime.now().isoformat()
        }
        
        # Track retry attempts for robustness
        self.retry_count = {}
        
        # Initialize ADK tool registry
        self.tool_registry = get_tool_registry()
        if not self.tool_registry.tools:
            config = {'api_keys': api_keys or {}}
            self.tool_registry.initialize_default_tools(config)
    
    def process_user_request(self, user_input: str, machine_mode: bool = False) -> str:
        """
        Main entry point for processing user requests.
        
        Args:
            user_input: Natural language user input
            machine_mode: If True, return pure JSON without summary
            
        Returns:
            Human-friendly response with JSON or pure JSON if machine_mode
        """
        try:
            # Detect user intent
            intent = self._detect_intent(user_input)
            
            # Process based on intent
            if intent == "add_tasks":
                return self._handle_add_tasks(user_input, machine_mode)
            elif intent == "plan_day":
                return self._handle_plan_day(user_input, machine_mode)
            elif intent == "check_reminders":
                return self._handle_check_reminders(user_input, machine_mode)
            elif intent == "update_task":
                return self._handle_update_task(user_input, machine_mode)
            elif intent == "set_preferences":
                return self._handle_set_preferences(user_input, machine_mode)
            else:
                return self._handle_general_query(user_input, machine_mode)
                
        except Exception as e:
            error_response = {
                "error": str(e),
                "status": "failed",
                "timestamp": datetime.now().isoformat()
            }
            
            if machine_mode:
                return json.dumps(error_response, indent=2)
            else:
                return f"I encountered an error: {str(e)}\\n\\n```json\\n{json.dumps(error_response, indent=2)}\\n```"
    
    def _detect_intent(self, user_input: str) -> str:
        """
        Detect user intent from natural language input.
        
        Args:
            user_input: User's natural language input
            
        Returns:
            Intent category as string
        """
        user_input_lower = user_input.lower()
        
        # Task creation/editing keywords
        if any(word in user_input_lower for word in [
            "add task", "create task", "new task", "i need to", "remember to",
            "todo", "task:", "schedule this"
        ]):
            return "add_tasks"
        
        # Planning keywords
        if any(word in user_input_lower for word in [
            "plan my day", "schedule my day", "create schedule", "organize my day",
            "what should i do", "plan today", "schedule tasks"
        ]):
            return "plan_day"
        
        # Reminder keywords
        if any(word in user_input_lower for word in [
            "reminders", "what's due", "upcoming tasks", "alerts", 
            "what's coming up", "check schedule"
        ]):
            return "check_reminders"
        
        # Task update keywords
        if any(word in user_input_lower for word in [
            "mark done", "complete task", "update task", "finished",
            "reschedule", "change due date"
        ]):
            return "update_task"
        
        # Preferences keywords
        if any(word in user_input_lower for word in [
            "set work hours", "change timezone", "update preferences",
            "focus time", "break length"
        ]):
            return "set_preferences"
        
        # Default to general query
        return "general_query"
    
    def _handle_add_tasks(self, user_input: str, machine_mode: bool) -> str:
        """Handle task creation requests."""
        try:
            # Use TaskCollector to extract tasks
            task_json = self.task_collector.process_user_input(user_input)
            task_data = json.loads(task_json)
            
            # Validate and add tasks to session
            if isinstance(task_data, list):
                new_tasks = task_data
            else:
                new_tasks = [task_data]
            
            # Check for missing essential fields and ask clarification
            missing_fields = self._check_missing_fields(new_tasks, user_input)
            if missing_fields and not machine_mode:
                return missing_fields
            
            # Add tasks to session state
            for task in new_tasks:
                task['id'] = self._generate_task_id(task)
                task['created_at'] = datetime.now().isoformat()
                self.session_state['tasks'].append(task)
            
            self.session_state['last_updated'] = datetime.now().isoformat()
            
            # Prepare response
            summary = f"Added {len(new_tasks)} task(s) to your list."
            
            if machine_mode:
                return json.dumps({"tasks": new_tasks, "status": "success"}, indent=2)
            else:
                return f"{summary}\\n\\n```json\\n{json.dumps(new_tasks, indent=2)}\\n```"
                
        except Exception as e:
            return self._handle_error("task creation", str(e), machine_mode)
    
    def _handle_plan_day(self, user_input: str, machine_mode: bool) -> str:
        """Handle daily planning requests."""
        try:
            # Determine target date
            target_date = self._extract_date_from_input(user_input) or date.today().isoformat()
            
            # Get tasks that need scheduling
            tasks_to_schedule = [
                task for task in self.session_state['tasks']
                if task.get('id') not in [c['task_id'] for c in self.session_state['completed']]
            ]
            
            if not tasks_to_schedule:
                no_tasks_msg = "No tasks to schedule. Add some tasks first!"
                if machine_mode:
                    return json.dumps({"message": no_tasks_msg, "schedule": None}, indent=2)
                else:
                    return no_tasks_msg
            
            # Determine if knowledge insights are needed
            knowledge_queries = self._determine_knowledge_needs(tasks_to_schedule)
            knowledge_insights = []
            
            if knowledge_queries:
                knowledge_json = self.knowledge_agent.fetch_insights(
                    knowledge_queries, 
                    self.session_state['preferences'].get('location'),
                    tasks_to_schedule
                )
                knowledge_insights = json.loads(knowledge_json)
            
            # Create schedule using SchedulePlanner
            schedule_json = self.schedule_planner.create_schedule(
                tasks_to_schedule,
                self.session_state['preferences'],
                self.session_state['blocked_times'],
                knowledge_insights,
                str(target_date),
                self.session_state['preferences']['timezone']
            )
            
            schedule_data = json.loads(schedule_json)
            
            # Save schedule to session
            self.session_state['schedules'].append({
                "date": target_date,
                "schedule": schedule_data,
                "created_at": datetime.now().isoformat()
            })
            self.session_state['last_updated'] = datetime.now().isoformat()
            
            # Prepare response
            scheduled_count = len(schedule_data.get('blocks', []))
            unscheduled_count = len(schedule_data.get('unscheduled', []))
            summary = f"Created schedule for {target_date} with {scheduled_count} time blocks. {unscheduled_count} tasks couldn't be scheduled."
            
            if machine_mode:
                return schedule_json
            else:
                return f"{summary}\\n\\n```json\\n{schedule_json}\\n```"
                
        except Exception as e:
            return self._handle_error("day planning", str(e), machine_mode)
    
    def _handle_check_reminders(self, user_input: str, machine_mode: bool) -> str:
        """Handle reminder checking requests."""
        try:
            # Get current schedule
            current_schedule = self._get_current_schedule()
            
            if not current_schedule:
                no_schedule_msg = "No schedule found for today. Plan your day first!"
                if machine_mode:
                    return json.dumps({"message": no_schedule_msg, "reminders": None}, indent=2)
                else:
                    return no_schedule_msg
            
            # Check reminders using ReminderAgent
            reminders_json = self.reminder_agent.process_reminder_tick(
                current_schedule,
                self.session_state['tasks'],
                self.session_state['preferences']
            )
            
            reminders_data = json.loads(reminders_json)
            
            # Prepare response
            alert_count = len(reminders_data.get('alerts', []))
            overdue_count = len(reminders_data.get('overdue', []))
            
            if alert_count > 0 or overdue_count > 0:
                summary = f"You have {alert_count} upcoming task(s) and {overdue_count} overdue task(s)."
            else:
                summary = "No urgent reminders right now. You're on track!"
            
            if machine_mode:
                return reminders_json
            else:
                return f"{summary}\\n\\n```json\\n{reminders_json}\\n```"
                
        except Exception as e:
            return self._handle_error("reminder checking", str(e), machine_mode)
    
    def _handle_update_task(self, user_input: str, machine_mode: bool) -> str:
        """Handle task update requests."""
        try:
            # Extract task identifier and update type
            update_info = self._parse_task_update(user_input)
            
            if not update_info:
                error_msg = "Could not understand task update request. Please specify which task and what to change."
                if machine_mode:
                    return json.dumps({"error": error_msg}, indent=2)
                else:
                    return error_msg
            
            task_id = update_info['task_id']
            update_type = update_info['type']
            
            # Find and update task
            task = self._find_task_by_id(task_id)
            if not task:
                error_msg = f"Task with ID '{task_id}' not found."
                if machine_mode:
                    return json.dumps({"error": error_msg}, indent=2)
                else:
                    return error_msg
            
            # Initialize summary
            summary = "Task updated successfully."
            
            if update_type == "mark_done":
                self._mark_task_complete(task_id)
                summary = f"Marked task '{task['title']}' as complete."
            elif update_type == "reschedule":
                new_date = update_info.get('new_date')
                task['due_date'] = new_date
                summary = f"Rescheduled task '{task['title']}' to {new_date}."
            
            self.session_state['last_updated'] = datetime.now().isoformat()
            
            if machine_mode:
                return json.dumps({"status": "success", "message": summary}, indent=2)
            else:
                return summary
                
        except Exception as e:
            return self._handle_error("task update", str(e), machine_mode)
    
    def _handle_set_preferences(self, user_input: str, machine_mode: bool) -> str:
        """Handle preference setting requests."""
        try:
            # Parse preferences from input
            new_prefs = self._parse_preferences(user_input)
            
            # Update session preferences
            for key, value in new_prefs.items():
                if key in self.session_state['preferences']:
                    self.session_state['preferences'][key] = value
            
            self.session_state['last_updated'] = datetime.now().isoformat()
            
            summary = f"Updated {len(new_prefs)} preference(s)."
            
            if machine_mode:
                return json.dumps({"preferences": self.session_state['preferences'], "status": "success"}, indent=2)
            else:
                return f"{summary}\\n\\n```json\\n{json.dumps(self.session_state['preferences'], indent=2)}\\n```"
                
        except Exception as e:
            return self._handle_error("preference setting", str(e), machine_mode)
    
    def _handle_general_query(self, user_input: str, machine_mode: bool) -> str:
        """Handle general queries and information requests."""
        try:
            # Use KnowledgeAgent for general information
            knowledge_json = self.knowledge_agent.fetch_insights([user_input])
            knowledge_data = json.loads(knowledge_json)
            
            if machine_mode:
                return knowledge_json
            else:
                if knowledge_data and knowledge_data[0].get('summary'):
                    summary = knowledge_data[0]['summary']
                    return f"Here's what I found: {summary}\\n\\n```json\\n{knowledge_json}\\n```"
                else:
                    return f"I couldn't find specific information about that.\\n\\n```json\\n{knowledge_json}\\n```"
                
        except Exception as e:
            return self._handle_error("information lookup", str(e), machine_mode)
    
    # Helper methods
    
    def _check_missing_fields(self, tasks: List[Dict[str, Any]], user_input: str) -> Optional[str]:
        """Check if essential fields are missing and return clarification question."""
        for task in tasks:
            # Check if user mentioned scheduling but no due_date
            if any(word in user_input.lower() for word in ['schedule', 'today', 'tomorrow']) and not task.get('due_date'):
                return f"When would you like to schedule '{task['title']}'? Please specify a date or time."
        
        return None
    
    def _determine_knowledge_needs(self, tasks: List[Dict[str, Any]]) -> List[str]:
        """Determine what knowledge insights are needed for scheduling."""
        queries = []
        
        # Check for outdoor tasks - need weather
        if any('outdoor' in task.get('tags', []) for task in tasks):
            queries.append("weather forecast for outdoor activities")
        
        # Check for travel tasks - need traffic info
        if any(tag in ['travel', 'commute'] for task in tasks for tag in task.get('tags', [])):
            queries.append("traffic and travel conditions")
        
        # Check task types for productivity insights
        task_types = set()
        for task in tasks:
            tags = task.get('tags', [])
            if 'work' in tags:
                task_types.add('analytical')
            if any(tag in tags for tag in ['creative', 'design']):
                task_types.add('creative')
        
        if task_types:
            queries.extend([f"productivity timing for {task_type} work" for task_type in task_types])
        
        return queries
    
    def _get_current_schedule(self) -> Optional[Dict[str, Any]]:
        """Get the schedule for today."""
        today = date.today().isoformat()
        
        for schedule_entry in reversed(self.session_state['schedules']):
            if schedule_entry['date'] == today:
                return schedule_entry['schedule']
        
        return None
    
    def _extract_date_from_input(self, user_input: str) -> Optional[str]:
        """Extract target date from user input."""
        user_input_lower = user_input.lower()
        
        if 'today' in user_input_lower:
            return date.today().isoformat()
        elif 'tomorrow' in user_input_lower:
            return (date.today().replace(day=date.today().day + 1)).isoformat()
        
        # TODO: Add more sophisticated date parsing
        return None
    
    def _generate_task_id(self, task: Dict[str, Any]) -> str:
        """Generate a unique task ID."""
        title = task.get('title', 'task')
        slug = title.lower().replace(' ', '-').replace('_', '-')
        slug = ''.join(c for c in slug if c.isalnum() or c == '-')[:20]
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        return f"{slug}-{timestamp}"
    
    def _parse_task_update(self, user_input: str) -> Optional[Dict[str, Any]]:
        """Parse task update information from user input."""
        # This is a simplified parser - in real implementation, use more sophisticated NLP
        user_input_lower = user_input.lower()
        
        if 'mark done' in user_input_lower or 'complete' in user_input_lower:
            # Extract task identifier (simplified - just take the first task for now)
            if self.session_state['tasks']:
                return {
                    'task_id': self.session_state['tasks'][-1]['id'],
                    'type': 'mark_done'
                }
        
        return None
    
    def _find_task_by_id(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Find a task by its ID."""
        for task in self.session_state['tasks']:
            if task.get('id') == task_id:
                return task
        return None
    
    def _mark_task_complete(self, task_id: str):
        """Mark a task as complete."""
        completion_record = {
            'task_id': task_id,
            'completed_at': datetime.now().isoformat()
        }
        self.session_state['completed'].append(completion_record)
    
    def _parse_preferences(self, user_input: str) -> Dict[str, Any]:
        """Parse preference updates from user input."""
        prefs = {}
        user_input_lower = user_input.lower()
        
        # Parse work hours
        if 'work hours' in user_input_lower:
            # Simplified parsing - in real implementation, use regex
            if '9' in user_input and '5' in user_input:
                prefs['work_hours'] = {"start": "09:00", "end": "17:00"}
        
        # Parse focus time
        if 'focus' in user_input_lower and 'minutes' in user_input_lower:
            import re
            match = re.search(r'(\\d+)\\s*minutes?', user_input_lower)
            if match:
                prefs['preferred_focus_minutes'] = int(match.group(1))
        
        return prefs
    
    def _handle_error(self, operation: str, error_msg: str, machine_mode: bool) -> str:
        """Handle errors with retry logic."""
        error_response = {
            "error": error_msg,
            "operation": operation,
            "status": "failed",
            "timestamp": datetime.now().isoformat()
        }
        
        if machine_mode:
            return json.dumps(error_response, indent=2)
        else:
            return f"I encountered an error during {operation}: {error_msg}\\n\\n```json\\n{json.dumps(error_response, indent=2)}\\n```"
    
    def get_session_state(self) -> Dict[str, Any]:
        """Get current session state."""
        return self.session_state.copy()
    
    def set_session_state(self, state: Dict[str, Any]):
        """Set session state (for loading saved sessions)."""
        self.session_state = state