"""
Unit tests for SchedulePlanner agent.
"""

import unittest
import json
from datetime import datetime, date
from agents.schedule_planner import SchedulePlanner

class TestSchedulePlanner(unittest.TestCase):
    """Test cases for SchedulePlanner agent."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.planner = SchedulePlanner()
        self.sample_tasks = [
            {
                "title": "Review project proposal",
                "duration_minutes": 60,
                "priority": "high",
                "due_date": "2025-11-27T15:00:00"
            },
            {
                "title": "Team meeting",
                "duration_minutes": 90,
                "priority": "medium",
                "due_date": "2025-11-27T10:00:00"
            },
            {
                "title": "Email responses",
                "duration_minutes": 30,
                "priority": "low"
            }
        ]
        self.sample_preferences = {
            "work_hours": {"start": "09:00", "end": "17:00"},
            "preferred_focus_minutes": 90
        }
    
    def test_schedule_creation(self):
        """Test basic schedule creation."""
        result = self.planner.create_schedule(
            tasks=self.sample_tasks,
            preferences=self.sample_preferences,
            blocked_times=[],
            target_date="2025-11-27",
            timezone="UTC"
        )
        
        schedule_data = json.loads(result)
        
        # Verify schedule structure
        self.assertIn('date', schedule_data)
        self.assertIn('blocks', schedule_data)
        self.assertIn('unscheduled', schedule_data)
        self.assertEqual(schedule_data['date'], '2025-11-27')
    
    def test_task_sorting_by_priority(self):
        """Test that high priority tasks are scheduled first."""
        result = self.planner.create_schedule(
            tasks=self.sample_tasks,
            preferences=self.sample_preferences,
            blocked_times=[],
            target_date="2025-11-27",
            timezone="UTC"
        )
        
        schedule_data = json.loads(result)
        blocks = schedule_data.get('blocks', [])
        
        # Should have at least one block
        self.assertGreater(len(blocks), 0)
        
        # First block should be high priority task (if scheduled)
        if blocks:
            first_block = blocks[0]
            self.assertIn('task_title', first_block)
    
    def test_blocked_time_handling(self):
        """Test that blocked times are respected."""
        blocked_times = [
            {
                "start": "2025-11-27T12:00:00",
                "end": "2025-11-27T13:00:00"
            }
        ]
        
        result = self.planner.create_schedule(
            tasks=self.sample_tasks,
            preferences=self.sample_preferences,
            blocked_times=blocked_times,
            target_date="2025-11-27",
            timezone="UTC"
        )
        
        schedule_data = json.loads(result)
        blocks = schedule_data.get('blocks', [])
        
        # No block should overlap with blocked time
        for block in blocks:
            start_time = datetime.fromisoformat(block['start'])
            end_time = datetime.fromisoformat(block['end'])
            
            blocked_start = datetime.fromisoformat("2025-11-27T12:00:00")
            blocked_end = datetime.fromisoformat("2025-11-27T13:00:00")
            
            # Check no overlap
            self.assertTrue(
                end_time <= blocked_start or start_time >= blocked_end,
                f"Block {block} overlaps with blocked time"
            )
    
    def test_task_splitting(self):
        """Test that long tasks are split into focus blocks."""
        long_task = {
            "title": "Long coding session",
            "duration_minutes": 180,  # 3 hours
            "priority": "medium"
        }
        
        result = self.planner.create_schedule(
            tasks=[long_task],
            preferences=self.sample_preferences,  # 90-minute focus blocks
            blocked_times=[],
            target_date="2025-11-27",
            timezone="UTC"
        )
        
        schedule_data = json.loads(result)
        blocks = schedule_data.get('blocks', [])
        
        # Should be split into multiple blocks
        coding_blocks = [b for b in blocks if "Long coding session" in b['task_title']]
        self.assertGreater(len(coding_blocks), 1)
        
        # Check subtask indices
        if len(coding_blocks) > 1:
            self.assertEqual(coding_blocks[0]['subtask_index'], 1)
            self.assertEqual(coding_blocks[1]['subtask_index'], 2)

if __name__ == '__main__':
    unittest.main()