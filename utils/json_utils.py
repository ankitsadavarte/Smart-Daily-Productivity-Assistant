"""
JSON utilities for the Smart Daily Productivity Assistant.
Handles datetime serialization and other JSON-related operations.
"""

import json
from datetime import datetime, date
from typing import Any

class DateTimeEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles datetime objects."""
    
    def default(self, obj: Any) -> Any:
        """Convert datetime objects to ISO format strings."""
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, date):
            return obj.isoformat()
        return super().default(obj)

def safe_json_dumps(obj: Any, **kwargs) -> str:
    """
    JSON dumps with datetime handling.
    
    Args:
        obj: Object to serialize
        **kwargs: Additional arguments for json.dumps
        
    Returns:
        JSON string with datetime objects properly serialized
    """
    return json.dumps(obj, cls=DateTimeEncoder, **kwargs)