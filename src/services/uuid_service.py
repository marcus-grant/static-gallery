"""UUID generation service for photos."""

import base64
from datetime import datetime
from typing import Optional, Dict

from src.util.uuidv7 import uuid7


def generate_photo_uuid(timestamp: Optional[datetime], camera_info: Dict, filename: str) -> str:
    """Generate a Base32-encoded UUIDv7 from photo metadata."""
    # Convert datetime to milliseconds for RFC 9562 compliance
    if timestamp:
        timestamp_ms = int(timestamp.timestamp() * 1000)
        photo_uuid = uuid7(timestamp_ms)
    else:
        photo_uuid = uuid7()
    
    # Convert to Base32 (26 characters)
    uuid_bytes = photo_uuid.bytes
    base32_str = base64.b32encode(uuid_bytes).decode('ascii').rstrip('=')
    
    return base32_str