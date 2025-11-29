"""
TaskCollector Agent - Converts natural language to structured task JSON.
This agent strictly follows the TaskSchema and returns only valid JSON.
"""

import json
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any, Union, Optional
from dateutil.parser import parse as parse_date
from schemas.task_schema import Task, TaskList

class TaskCollector:
    """
    TaskCollector Agent - Converts natural language task descriptions 
    into structured JSON matching the TaskSchema.
    """
    
    PRIORITY_MAPPING = {
        # High priority keywords
        "urgent": "high",
        "asap": "high", 
        "critical": "high",
        "emergency": "high",
        "immediately": "high",
        
        # Low priority keywords
        "someday": "low",
        "when possible": "low",
        "eventually": "low",
        "nice to have": "low",
        
        # Medium is default for everything else
    }
    
    DURATION_PATTERNS = {
        r'(\d+)\s*hour?s?': lambda x: int(x) * 60,
        r'(\d+)\s*min(?:ute)?s?': lambda x: int(x),
        r'(\d+)h\s*(\d+)m': lambda h, m: int(h) * 60 + int(m),
        r'(\d+)h': lambda x: int(x) * 60,
        r'(\d+)m': lambda x: int(x),
    }
    
    def __init__(self):
        """Initialize TaskCollector with system prompt behavior."""
        self.system_prompt = """You are TaskCollector — a strict JSON extractor. Always return ONLY JSON with fields defined in the TaskSchema. For multiple tasks, output a JSON array."""
    
    def extract_tasks(self, user_input: str) -> Union[List[Dict], Dict]:
        """
        Main method to convert natural language input to task JSON(s).
        
        Args:
            user_input: Natural language description of task(s)
            
        Returns:
            Dictionary or list of dictionaries matching TaskSchema
        """
        # Detect multiple tasks
        tasks = self._split_multiple_tasks(user_input)
        
        if len(tasks) == 1:
            return self._process_single_task(tasks[0])
        else:
            return [self._process_single_task(task) for task in tasks]
    
    def _split_multiple_tasks(self, text: str) -> List[str]:
        """Split input into individual tasks if multiple are present."""
        # Check for numbered lists without line breaks (e.g., "1. Task 2. Task 3. Task")
        if re.search(r'\d+\.\s+[^\n]+\s+\d+\.', text):
            # Split by number patterns
            parts = re.split(r'\s+(?=\d+\.)', text)
            tasks = []
            for part in parts:
                # Remove the number prefix
                task = re.sub(r'^\d+\.\s*', '', part).strip()
                if task:
                    tasks.append(task)
            return tasks if len(tasks) > 1 else [text.strip()]
        
        # Common separators for multiple tasks
        separators = [
            r'\n\d+\.',  # Numbered lists with line breaks
            r'\n-\s*',   # Dash lists
            r'\n\*\s*',  # Bullet lists
            r'\band\s+',  # "and" separator
            r',\s*then\s*',  # "then" separator
            r';\s*'      # Semicolon separator
        ]
        
        for pattern in separators:
            if re.search(pattern, text, re.IGNORECASE):
                # Split by pattern and clean up
                parts = re.split(pattern, text)
                return [part.strip() for part in parts if part.strip()]
        
        # No multiple tasks detected
        return [text.strip()]
    
    def _process_single_task(self, task_text: str) -> Dict[str, Any]:
        """Process a single task description into TaskSchema format."""
        result = {
            "title": self._extract_title(task_text),
            "description": self._extract_description(task_text),
            "priority": self._extract_priority(task_text),
            "due_date": self._extract_due_date(task_text),
            "duration_minutes": self._extract_duration(task_text),
            "tags": self._extract_tags(task_text),
            "recurring": self._extract_recurring(task_text)
        }
        
        # Remove None values for cleaner JSON
        return {k: v for k, v in result.items() if v is not None}
    
    def _extract_title(self, text: str) -> str:
        """Extract task title (first meaningful phrase or entire text if short)."""
        # For short texts, use the entire text to preserve natural language
        if len(text) <= 50:
            return text.strip()
        
        # Only remove prefixes for longer texts to extract core task
        cleaned_text = re.sub(r'^(task:?\s*|todo:?\s*)', '', text, flags=re.IGNORECASE)
        
        # Extract first sentence/clause
        sentences = re.split(r'[.!?;]|\s+by\s+|\s+due\s+|\s+for\s+\d+', cleaned_text)
        return sentences[0].strip() if sentences else cleaned_text.strip()
    
    def _extract_description(self, text: str) -> Optional[str]:
        """Extract detailed description if present."""
        title = self._extract_title(text)
        
        # If title is much shorter than full text, rest is description
        if len(text) > len(title) + 20:
            description = text.replace(title, '', 1).strip()
            # Clean up common separators
            description = re.sub(r'^[.,:;-]+\s*', '', description)
            return description if description else None
        
        return None
    
    def _extract_priority(self, text: str) -> Optional[str]:
        """Extract priority based on keywords."""
        text_lower = text.lower()
        
        for keyword, priority in self.PRIORITY_MAPPING.items():
            if keyword in text_lower:
                return priority
        
        # Check for emphasis patterns
        if re.search(r'!!+|URGENT|ASAP', text):
            return "high"
        elif re.search(r'maybe|might|could|optional', text_lower):
            return "low"
        
        return "medium"  # Default
    
    def _extract_due_date(self, text: str) -> Optional[str]:
        """Extract due date from natural language."""
        # Common date patterns
        date_patterns = [
            r'by\s+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'due\s+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'on\s+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'by\s+(today|tomorrow|monday|tuesday|wednesday|thursday|friday|saturday|sunday)',
            r'due\s+(today|tomorrow|monday|tuesday|wednesday|thursday|friday|saturday|sunday)',
            r'(today|tomorrow|monday|tuesday|wednesday|thursday|friday|saturday|sunday)',
            r'by\s+(next\s+week|next\s+month)',
            r'in\s+(\d+)\s+days?',
            r'(\d{4}-\d{2}-\d{2})',  # ISO format
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                date_str = match.group(1)
                try:
                    # Parse relative dates
                    if date_str.lower() == 'today':
                        return datetime.now().isoformat()
                    elif date_str.lower() == 'tomorrow':
                        return (datetime.now() + timedelta(days=1)).isoformat()
                    elif 'next week' in date_str.lower():
                        return (datetime.now() + timedelta(weeks=1)).isoformat()
                    elif 'next month' in date_str.lower():
                        return (datetime.now() + timedelta(days=30)).isoformat()
                    elif date_str.lower() in ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']:
                        # Find next occurrence of this weekday
                        return self._next_weekday(date_str).isoformat()
                    else:
                        # Try to parse the date string
                        parsed_date = parse_date(date_str, fuzzy=True)
                        return parsed_date.isoformat()
                except:
                    continue
        
        return None
    
    def _next_weekday(self, weekday_name: str) -> datetime:
        """Find the next occurrence of a given weekday."""
        weekdays = {
            'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
            'friday': 4, 'saturday': 5, 'sunday': 6
        }
        
        target_day = weekdays[weekday_name.lower()]
        current_day = datetime.now().weekday()
        
        days_ahead = target_day - current_day
        if days_ahead <= 0:  # Target day already happened this week
            days_ahead += 7
        
        return datetime.now() + timedelta(days=days_ahead)
    
    def _extract_duration(self, text: str) -> Optional[int]:
        """Extract duration in minutes from text."""
        for pattern, converter in self.DURATION_PATTERNS.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    if len(match.groups()) == 2:  # e.g., "2h 30m"
                        return converter(*match.groups())
                    else:
                        return converter(match.group(1))
                except:
                    continue
        
        return None
    
    def _extract_tags(self, text: str) -> List[str]:
        """Extract 1-4 relevant tags from the task text."""
        # Common tag patterns
        tag_keywords = {
            'work': ['work', 'office', 'meeting', 'project', 'deadline', 'client'],
            'personal': ['personal', 'home', 'family', 'hobby'],
            'health': ['exercise', 'gym', 'doctor', 'medication', 'health'],
            'shopping': ['buy', 'purchase', 'shop', 'grocery', 'store'],
            'communication': ['call', 'email', 'text', 'message', 'contact'],
            'travel': ['travel', 'trip', 'flight', 'hotel', 'vacation'],
            'finance': ['pay', 'bill', 'bank', 'money', 'budget'],
            'learning': ['learn', 'study', 'course', 'book', 'research'],
            'maintenance': ['fix', 'repair', 'clean', 'maintain', 'organize']
        }
        
        text_lower = text.lower()
        tags = []
        
        for tag, keywords in tag_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                tags.append(tag)
        
        # Limit to 4 tags maximum
        return tags[:4]
    
    def _extract_recurring(self, text: str) -> Optional[str]:
        """Extract recurring pattern from text."""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['daily', 'every day', 'each day']):
            return 'daily'
        elif any(word in text_lower for word in ['weekly', 'every week', 'each week']):
            return 'weekly'
        elif any(word in text_lower for word in ['monthly', 'every month', 'each month']):
            return 'monthly'
        
        return None
    
    def validate_task_json(self, task_dict: Dict) -> bool:
        """Validate that the task dictionary matches TaskSchema."""
        try:
            Task(**task_dict)
            return True
        except Exception:
            return False
    
    def process_user_input(self, user_input: str) -> str:
        """
        Main entry point that returns JSON string following the system prompt.
        Returns ONLY JSON as specified in the system prompt.
        """
        try:
            result = self.extract_tasks(user_input)
            return json.dumps(result, indent=2)
        except Exception as e:
            # Fallback - return basic task structure
            fallback = {
                "title": user_input[:100],
                "description": None,
                "priority": "medium",
                "due_date": None,
                "duration_minutes": None,
                "tags": [],
                "recurring": None
            }
            return json.dumps(fallback, indent=2)