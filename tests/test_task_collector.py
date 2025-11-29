"""
Unit tests for TaskCollector agent.
"""

import unittest
import json
from agents.task_collector import TaskCollector

class TestTaskCollector(unittest.TestCase):
    """Test cases for TaskCollector agent."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.collector = TaskCollector()
    
    def test_single_task_extraction(self):
        """Test extracting a single task."""
        user_input = "I need to call the dentist by Friday"
        result = self.collector.process_user_input(user_input)
        task_data = json.loads(result)
        
        self.assertEqual(task_data['title'], "I need to call the dentist by Friday")
        self.assertIn('communication', task_data.get('tags', []))
        self.assertIsNotNone(task_data.get('due_date'))
    
    def test_multiple_tasks_extraction(self):
        """Test extracting multiple tasks."""
        user_input = "1. Buy groceries 2. Call mom 3. Finish project report"
        result = self.collector.process_user_input(user_input)
        task_data = json.loads(result)
        
        self.assertIsInstance(task_data, list)
        self.assertEqual(len(task_data), 3)
        self.assertEqual(task_data[0]['title'], "Buy groceries")
        self.assertEqual(task_data[1]['title'], "Call mom")
        self.assertEqual(task_data[2]['title'], "Finish project report")
    
    def test_priority_extraction(self):
        """Test priority extraction from text."""
        # High priority
        urgent_input = "URGENT: Fix the server issue"
        result = json.loads(self.collector.process_user_input(urgent_input))
        self.assertEqual(result['priority'], 'high')
        
        # Low priority
        someday_input = "Someday I should organize my bookshelf"
        result = json.loads(self.collector.process_user_input(someday_input))
        self.assertEqual(result['priority'], 'low')
    
    def test_duration_extraction(self):
        """Test duration extraction from text."""
        # Test various duration formats
        test_cases = [
            ("2 hour meeting preparation", 120),
            ("30 minute phone call", 30),
            ("1h 30m presentation", 90),
            ("Quick 15min standup", 15)
        ]
        
        for input_text, expected_duration in test_cases:
            result = json.loads(self.collector.process_user_input(input_text))
            self.assertEqual(result.get('duration_minutes'), expected_duration)
    
    def test_tag_extraction(self):
        """Test tag extraction from text."""
        work_input = "Prepare quarterly project meeting with client"
        result = json.loads(self.collector.process_user_input(work_input))
        tags = result.get('tags', [])
        
        self.assertIn('work', tags)
        # Should limit to 4 tags max
        self.assertLessEqual(len(tags), 4)
    
    def test_recurring_pattern_extraction(self):
        """Test recurring pattern extraction."""
        daily_input = "Daily standup meeting every morning"
        result = json.loads(self.collector.process_user_input(daily_input))
        self.assertEqual(result.get('recurring'), 'daily')
        
        weekly_input = "Weekly team review meeting"
        result = json.loads(self.collector.process_user_input(weekly_input))
        self.assertEqual(result.get('recurring'), 'weekly')

if __name__ == '__main__':
    unittest.main()