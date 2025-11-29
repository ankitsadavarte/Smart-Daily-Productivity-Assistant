"""
SchedulePlanner Agent - Generates conflict-free daily schedules.
This agent creates time blocks, respects user preferences, and handles task splitting.
"""

import json
from datetime import datetime, timedelta, time, date
from typing import List, Dict, Any, Tuple, Optional
from schemas.task_schema import Task
from schemas.schedule_schema import DailySchedule, ScheduleBlock, UnscheduledTask

class SchedulePlanner:
    """
    SchedulePlanner Agent - Produces a conflict-free schedule as JSON 
    using the ScheduleSchema.
    """
    
    def __init__(self):
        """Initialize SchedulePlanner with system prompt behavior."""
        self.system_prompt = """You are SchedulePlanner — produce a conflict-free schedule as JSON using the ScheduleSchema. Split tasks into subtasks using preferred_focus_minutes. Respect working_hours, blocked_times. If a task cannot fit, add it to `unscheduled` with a reason."""
    
    def create_schedule(
        self, 
        tasks: List[Dict[str, Any]], 
        preferences: Dict[str, Any], 
        blocked_times: List[Dict[str, Any]], 
        knowledge_insights: Optional[List[Dict[str, Any]]] = None,
        target_date: Optional[str] = None,
        timezone: str = "UTC"
    ) -> str:
        """
        Main method to create a daily schedule.
        
        Args:
            tasks: List of task dictionaries
            preferences: User preferences (work_hours, preferred_focus_minutes, etc.)
            blocked_times: List of unavailable time slots
            knowledge_insights: External insights that might affect scheduling
            target_date: Date to schedule for (YYYY-MM-DD format)
            timezone: Timezone for the schedule
            
        Returns:
            JSON string matching ScheduleSchema
        """
        try:
            if target_date is None:
                target_date_obj = datetime.now().date()
            else:
                target_date_obj = datetime.fromisoformat(target_date).date()
            
            # Sort tasks by priority and due date
            sorted_tasks = self._sort_tasks_by_priority(tasks)
            
            # Get available time slots
            available_slots = self._get_available_time_slots(
                target_date_obj, preferences, blocked_times, timezone
            )
            
            # Schedule tasks into time blocks
            scheduled_blocks = []
            unscheduled_tasks = []
            
            for task in sorted_tasks:
                blocks, success = self._schedule_task(
                    task, available_slots, preferences, knowledge_insights, timezone
                )
                
                if success:
                    scheduled_blocks.extend(blocks)
                    # Remove used time slots
                    for block in blocks:
                        available_slots = self._remove_time_slot(
                            available_slots, block['start'], block['end']
                        )
                else:
                    reason = self._get_unscheduled_reason(task, available_slots, preferences)
                    unscheduled_tasks.append({
                        "task_title": task.get('title', 'Untitled Task'),
                        "reason": reason
                    })
            
            # Create the final schedule
            schedule = DailySchedule(
                date=target_date_obj.isoformat(),
                time_zone=timezone,
                blocks=scheduled_blocks,
                unscheduled=unscheduled_tasks
            )
            
            return schedule.json(indent=2)
            
        except Exception as e:
            # Fallback schedule
            fallback_date = target_date if target_date else datetime.now().date().isoformat()
            fallback = {
                "date": fallback_date,
                "time_zone": timezone,
                "blocks": [],
                "unscheduled": [{"task_title": "Schedule creation failed", "reason": str(e)}]
            }
            return json.dumps(fallback, indent=2)
    
    def _sort_tasks_by_priority(self, tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Sort tasks by due date first, then priority."""
        def sort_key(task):
            # Due date priority (tasks with due dates come first)
            due_date = task.get('due_date')
            if due_date:
                try:
                    due_dt = datetime.fromisoformat(due_date.replace('Z', '+00:00'))
                    due_priority = due_dt.timestamp()
                except:
                    due_priority = float('inf')
            else:
                due_priority = float('inf')
            
            # Priority value (high=0, medium=1, low=2)
            priority_map = {"high": 0, "medium": 1, "low": 2}
            priority_value = priority_map.get(task.get('priority', 'medium'), 1)
            
            return (due_priority, priority_value)
        
        return sorted(tasks, key=sort_key)
    
    def _get_available_time_slots(
        self, 
        date: date, 
        preferences: Dict[str, Any], 
        blocked_times: List[Dict[str, Any]], 
        timezone: str
    ) -> List[Tuple[datetime, datetime]]:
        """Generate list of available time slots for the day."""
        # Get work hours from preferences
        work_hours = preferences.get('work_hours', {"start": "09:00", "end": "17:00"})
        start_time = datetime.combine(
            date, 
            time.fromisoformat(work_hours['start'])
        )
        end_time = datetime.combine(
            date, 
            time.fromisoformat(work_hours['end'])
        )
        
        # Start with the full work day as one slot
        available_slots = [(start_time, end_time)]
        
        # Remove blocked times
        for blocked in blocked_times:
            blocked_start = datetime.fromisoformat(blocked['start'])
            blocked_end = datetime.fromisoformat(blocked['end'])
            
            # Remove this blocked time from available slots
            available_slots = self._subtract_time_from_slots(
                available_slots, blocked_start, blocked_end
            )
        
        return available_slots
    
    def _subtract_time_from_slots(
        self, 
        slots: List[Tuple[datetime, datetime]], 
        block_start: datetime, 
        block_end: datetime
    ) -> List[Tuple[datetime, datetime]]:
        """Remove a blocked time period from available slots."""
        new_slots = []
        
        for slot_start, slot_end in slots:
            if block_end <= slot_start or block_start >= slot_end:
                # No overlap
                new_slots.append((slot_start, slot_end))
            elif block_start <= slot_start and block_end >= slot_end:
                # Blocked time completely covers this slot - remove it
                continue
            elif block_start > slot_start and block_end < slot_end:
                # Blocked time is in the middle - split into two slots
                new_slots.append((slot_start, block_start))
                new_slots.append((block_end, slot_end))
            elif block_start <= slot_start and block_end < slot_end:
                # Blocked time covers start of slot
                new_slots.append((block_end, slot_end))
            elif block_start > slot_start and block_end >= slot_end:
                # Blocked time covers end of slot
                new_slots.append((slot_start, block_start))
        
        return new_slots
    
    def _schedule_task(
        self, 
        task: Dict[str, Any], 
        available_slots: List[Tuple[datetime, datetime]], 
        preferences: Dict[str, Any], 
        knowledge_insights: Optional[List[Dict[str, Any]]], 
        timezone: str
    ) -> Tuple[List[Dict[str, Any]], bool]:
        """
        Schedule a single task into available time slots.
        
        Returns:
            Tuple of (scheduled_blocks, success_flag)
        """
        duration = task.get('duration_minutes', preferences.get('preferred_focus_minutes', 90))
        focus_minutes = preferences.get('preferred_focus_minutes', 90)
        
        # Split task into subtasks if needed
        subtasks = self._split_task_into_subtasks(task, duration, focus_minutes)
        
        scheduled_blocks = []
        
        for i, subtask_duration in enumerate(subtasks):
            # Find a suitable time slot
            slot = self._find_suitable_slot(
                subtask_duration, available_slots, task, knowledge_insights
            )
            
            if slot is None:
                # Cannot schedule this subtask
                return scheduled_blocks, False
            
            slot_start, slot_end = slot
            
            # Create the schedule block
            block_start = slot_start
            block_end = slot_start + timedelta(minutes=subtask_duration)
            
            # Add knowledge-based notes
            notes = self._generate_block_notes(task, knowledge_insights, block_start)
            
            block = {
                "start": block_start.isoformat(),
                "end": block_end.isoformat(),
                "task_title": task.get('title', 'Untitled Task'),
                "task_id": self._generate_task_id(task, block_start.date()),
                "subtask_index": i + 1,
                "notes": notes
            }
            
            scheduled_blocks.append(block)
            
            # Add break time if this isn't the last subtask
            if i < len(subtasks) - 1:
                break_duration = min(15, (slot_end - block_end).total_seconds() // 60)
                block_end += timedelta(minutes=break_duration)
        
        return scheduled_blocks, True
    
    def _split_task_into_subtasks(
        self, 
        task: Dict[str, Any], 
        total_duration: int, 
        focus_minutes: int
    ) -> List[int]:
        """Split a task into subtasks based on focus time preferences."""
        if total_duration <= focus_minutes:
            return [total_duration]
        
        # Calculate number of full focus blocks needed
        full_blocks = total_duration // focus_minutes
        remainder = total_duration % focus_minutes
        
        subtasks = [focus_minutes] * full_blocks
        if remainder > 0:
            subtasks.append(remainder)
        
        return subtasks
    
    def _find_suitable_slot(
        self, 
        duration_minutes: int, 
        available_slots: List[Tuple[datetime, datetime]], 
        task: Dict[str, Any], 
        knowledge_insights: Optional[List[Dict[str, Any]]]
    ) -> Optional[Tuple[datetime, datetime]]:
        """Find the first available slot that can fit the duration."""
        required_duration = timedelta(minutes=duration_minutes)
        
        for slot_start, slot_end in available_slots:
            slot_duration = slot_end - slot_start
            
            if slot_duration >= required_duration:
                # Check if knowledge insights suggest avoiding this time
                if self._is_time_suitable(slot_start, task, knowledge_insights):
                    return (slot_start, slot_end)
        
        return None
    
    def _is_time_suitable(
        self, 
        start_time: datetime, 
        task: Dict[str, Any], 
        knowledge_insights: Optional[List[Dict[str, Any]]]
    ) -> bool:
        """Check if a time slot is suitable based on knowledge insights."""
        if not knowledge_insights:
            return True
        
        task_tags = task.get('tags', [])
        
        for insight in knowledge_insights:
            impact = insight.get('suggested_schedule_impact', '')
            if impact and any(tag in impact.lower() for tag in task_tags):
                # This insight affects this task type
                if 'avoid' in impact.lower() and start_time.strftime('%H:%M') in impact:
                    return False
        
        return True
    
    def _generate_block_notes(
        self, 
        task: Dict[str, Any], 
        knowledge_insights: Optional[List[Dict[str, Any]]], 
        start_time: datetime
    ) -> Optional[str]:
        """Generate notes for a schedule block based on knowledge insights."""
        if not knowledge_insights:
            return None
        
        notes = []
        task_tags = task.get('tags', [])
        
        for insight in knowledge_insights:
            summary = insight.get('summary', '')
            impact = insight.get('suggested_schedule_impact', '')
            
            if summary and any(tag in summary.lower() for tag in task_tags):
                notes.append(f"{summary}")
            elif impact and start_time.strftime('%H') in impact:
                notes.append(f"{impact}")
        
        return '; '.join(notes) if notes else None
    
    def _generate_task_id(self, task: Dict[str, Any], date: date) -> str:
        """Generate a deterministic task ID."""
        title = task.get('title', 'task')
        # Create a slug from the title
        slug = title.lower().replace(' ', '-').replace('_', '-')
        slug = ''.join(c for c in slug if c.isalnum() or c == '-')[:20]
        return f"{slug}-{date.strftime('%Y%m%d')}"
    
    def _remove_time_slot(
        self, 
        slots: List[Tuple[datetime, datetime]], 
        used_start: str, 
        used_end: str
    ) -> List[Tuple[datetime, datetime]]:
        """Remove a used time slot from available slots."""
        used_start_dt = datetime.fromisoformat(used_start)
        used_end_dt = datetime.fromisoformat(used_end)
        
        return self._subtract_time_from_slots(slots, used_start_dt, used_end_dt)
    
    def _get_unscheduled_reason(
        self, 
        task: Dict[str, Any], 
        available_slots: List[Tuple[datetime, datetime]], 
        preferences: Dict[str, Any]
    ) -> str:
        """Generate a reason why a task couldn't be scheduled."""
        duration = task.get('duration_minutes', preferences.get('preferred_focus_minutes', 90))
        
        if not available_slots:
            return "No available time slots remaining"
        
        max_slot_duration = max(
            (slot[1] - slot[0]).total_seconds() // 60 
            for slot in available_slots
        )
        
        if duration > max_slot_duration:
            return f"Task requires {duration} minutes, but largest available slot is {int(max_slot_duration)} minutes"
        
        return "Could not find suitable time slot"