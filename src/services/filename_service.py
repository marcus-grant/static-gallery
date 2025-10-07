"""Human-readable chronological filename generation service."""

from datetime import datetime
from timezonefinder import TimezoneFinder
from zoneinfo import ZoneInfo

from src.models.photo import ProcessedPhoto, CameraInfo


def generate_photo_filename(photo: ProcessedPhoto, collection: str = "gallery") -> str:
    """Generate chronological filename from photo metadata.
    
    Format: collection-YYYYMMDDTHHmmss.sssZhhmm-camera-seq.jpg
    Example: wedding-20241005T143045.123Z0400-r5a-001.jpg
    
    Args:
        photo: ProcessedPhoto with EXIF metadata
        collection: Collection name (case-insensitive, converted to lowercase)
        
    Returns:
        Generated filename string
    """
    # Use collection from photo if available, otherwise use parameter
    collection_name = (photo.collection or collection).lower()
    
    # Get timezone-aware timestamp
    if photo.exif.timestamp and photo.exif.gps_latitude and photo.exif.gps_longitude:
        timezone_offset = get_timezone_from_gps(
            photo.exif.gps_latitude, 
            photo.exif.gps_longitude,
            photo.exif.timestamp
        )
    else:
        # Fallback to local timezone if no GPS
        local_tz = datetime.now().astimezone().tzinfo
        timezone_offset = local_tz.utcoffset(datetime.now()).total_seconds() / 3600
        timezone_offset = f"{int(timezone_offset):+03d}{int(abs(timezone_offset) % 1 * 60):02d}"
    
    # Format ISO timestamp
    timestamp_str = format_iso_timestamp(photo.exif.timestamp or datetime.now(), timezone_offset)
    
    # Get camera code
    camera_code = get_camera_code(photo.camera)
    
    # For now, use sequence 001 - will be enhanced for burst mode
    sequence = "001"
    
    # Get file extension
    extension = photo.path.suffix.lower()
    
    return f"{collection_name}-{timestamp_str}-{camera_code}-{sequence}{extension}"


def get_timezone_from_gps(latitude: float, longitude: float, timestamp: datetime) -> str:
    """Get timezone offset from GPS coordinates and date.
    
    Args:
        latitude: GPS latitude
        longitude: GPS longitude  
        timestamp: Photo timestamp for DST calculation
        
    Returns:
        Timezone offset string in format ±HHMM (e.g., "0400", "1030")
    """
    try:
        tf = TimezoneFinder()
        tz_name = tf.timezone_at(lat=latitude, lng=longitude)
        
        if not tz_name:
            # Fallback to UTC if timezone cannot be determined
            return "0000"
    except Exception:
        # Invalid coordinates or other errors - fallback to UTC
        return "0000"
        
    tz = ZoneInfo(tz_name)
    localized_dt = timestamp.replace(tzinfo=tz)
    offset_seconds = localized_dt.utcoffset().total_seconds()
    
    # Convert to ±HHMM format
    offset_hours = int(offset_seconds / 3600)
    offset_minutes = int(abs(offset_seconds) % 3600 / 60)
    
    return f"{offset_hours:+03d}{offset_minutes:02d}"


def format_iso_timestamp(dt: datetime, timezone_offset: str) -> str:
    """Format datetime as filename-safe ISO 8601 string.
    
    Args:
        dt: Datetime object
        timezone_offset: Timezone offset string (±HHMM)
        
    Returns:
        ISO timestamp in format: YYYYMMDDTHHmmss.sssZ±HHMM
    """
    # Format basic ISO string without colons/hyphens
    base_str = dt.strftime("%Y%m%dT%H%M%S")
    
    # Add milliseconds
    milliseconds = f"{dt.microsecond // 1000:03d}"
    
    # Add timezone offset with Z prefix
    return f"{base_str}.{milliseconds}Z{timezone_offset}"


def get_camera_code(camera_info: CameraInfo) -> str:
    """Extract 3-letter lowercase camera identifier.
    
    Args:
        camera_info: Camera make and model information
        
    Returns:
        3-letter lowercase camera code
    """
    if not camera_info.make and not camera_info.model:
        return "unk"  # unknown
        
    # Combine make and model
    combined = f"{camera_info.make or ''} {camera_info.model or ''}".strip()
    
    # Common camera mappings
    camera_mappings = {
        "canon eos r5": "r5a",
        "canon eos r6": "r6a", 
        "canon eos 5d": "5da",
        "canon eos 6d": "6da",
        "nikon d850": "d85",
        "nikon d750": "d75",
        "sony a7r": "a7r",
        "sony a7 iii": "a73",
        "iphone 15": "i15",
        "iphone 14": "i14",
        "iphone 13": "i13", 
        "iphone 12": "i12",
        "iphone": "iph",
    }
    
    combined_lower = combined.lower()
    
    # Check for exact matches first
    for key, code in camera_mappings.items():
        if key in combined_lower:
            return code
            
    # Fallback: take first 3 characters of combined string
    # Remove spaces and take first 3 alphanumeric characters
    clean = ''.join(c for c in combined_lower if c.isalnum())
    return (clean[:3] or "unk").ljust(3, 'x')[:3]