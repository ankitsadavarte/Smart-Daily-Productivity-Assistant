"""
Configuration settings for the Smart Daily Productivity Assistant.
"""

import os
from typing import Dict, Any

# Default configuration
DEFAULT_CONFIG = {
    "preferences": {
        "work_hours": {
            "start": "09:00",
            "end": "17:00"
        },
        "preferred_focus_minutes": 90,
        "alert_window_minutes": 60,
        "timezone": "UTC",
        "location": None
    },
    "api_keys": {
        "weather_api_key": os.getenv("WEATHER_API_KEY"),
        "search_api_key": os.getenv("SEARCH_API_KEY"),
        "google_api_key": os.getenv("GOOGLE_API_KEY", "AIzaSyAKLKZruyFTRtP2cLqE2oIYHQXAm9Be8Dg")
    },
    "session": {
        "auto_save": True,
        "save_interval_minutes": 5,
        "max_history_days": 30
    },
    "agents": {
        "task_collector": {
            "max_tags_per_task": 4,
            "default_priority": "medium"
        },
        "schedule_planner": {
            "default_break_minutes": 15,
            "max_consecutive_blocks": 4
        },
        "reminder_agent": {
            "default_alert_window_minutes": 60,
            "snooze_intervals": [5, 10, 15, 30]
        },
        "knowledge_agent": {
            "max_summary_words": 40,
            "cache_duration_hours": 2
        }
    }
}

def get_config() -> Dict[str, Any]:
    """Get current configuration."""
    return DEFAULT_CONFIG.copy()

def update_config(updates: Dict[str, Any]) -> Dict[str, Any]:
    """Update configuration with new values."""
    config = get_config()
    
    def deep_update(base_dict, update_dict):
        for key, value in update_dict.items():
            if isinstance(value, dict) and key in base_dict and isinstance(base_dict[key], dict):
                deep_update(base_dict[key], value)
            else:
                base_dict[key] = value
    
    deep_update(config, updates)
    return config