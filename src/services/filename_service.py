"""Human-readable chronological filename generation service."""

from datetime import datetime
from timezonefinder import TimezoneFinder
from zoneinfo import ZoneInfo

from src.models.photo import ProcessedPhoto, CameraInfo

# Lexically-ordered base32 alphabet for counter system
LEXICAL_BASE32 = "0123456789ABCDEFGHIJKLMNOPQRSTUV"


def generate_photo_filename(photo: ProcessedPhoto, collection: str = "gallery", 
                          existing_filenames: set = None) -> str:
    """Generate chronological filename from photo metadata.
    
    Format: collection-YYYYMMDDTHHMMSS-camera-counter.jpg
    Example: wedding-20241005T143045-r5a-0.jpg
    
    Args:
        photo: ProcessedPhoto with EXIF metadata
        collection: Collection name (case-insensitive, converted to lowercase)
        existing_filenames: Set of existing filenames to avoid duplicates
        
    Returns:
        Generated filename string
    """
    # Use collection from photo if available, otherwise use parameter
    collection_name = (photo.collection or collection).lower()
    
    # Format UTC timestamp (no timezone processing)
    timestamp_str = format_iso_timestamp(photo.exif.timestamp or datetime.now())
    
    # Get camera code
    camera_code = get_camera_code(photo.camera)
    
    # Get file extension
    extension = photo.path.suffix.lower()
    
    # Generate base32 counter to avoid duplicates
    sequence = 1
    if existing_filenames:
        base_name = f"{collection_name}-{timestamp_str}-{camera_code}"
        while True:
            counter_char = LEXICAL_BASE32[sequence - 1]  # Convert to 0-indexed
            filename = f"{base_name}-{counter_char}{extension}"
            if filename not in existing_filenames:
                break
            sequence += 1
            if sequence > 32:  # Safety check for base32 range
                raise ValueError(f"Too many photos with same timestamp and camera: {base_name}")
    else:
        counter_char = LEXICAL_BASE32[0]  # First photo gets '0'
    
    filename = f"{collection_name}-{timestamp_str}-{camera_code}-{counter_char}{extension}"
    
    return filename


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


def format_iso_timestamp(dt: datetime) -> str:
    """Format datetime as filename-safe UTC timestamp to the second.
    
    Args:
        dt: Datetime object (assumed to be UTC)
        
    Returns:
        UTC timestamp in format: YYYYMMDDTHHMMSS (to the second only)
    """
    # Format basic ISO string without colons/hyphens (UTC only, to the second)
    return dt.strftime("%Y%m%dT%H%M%S")


def extract_subsecond_timing(photo: ProcessedPhoto) -> float:
    """Extract subsecond timing for ordering photos within the same second.
    
    Hierarchy:
    1. EXIF timestamp microseconds (if present)
    2. EXIF subsecond tag (if present)
    3. Return 0.0 for no subsecond data (will use filename/filesystem hints)
    
    Args:
        photo: ProcessedPhoto with EXIF data
        
    Returns:
        Subsecond timing as float (0.0 to 0.999)
    """
    # Priority 1: EXIF timestamp microseconds
    if photo.exif.timestamp and photo.exif.timestamp.microsecond > 0:
        return photo.exif.timestamp.microsecond / 1_000_000
    
    # Priority 2: EXIF subsecond tag
    if photo.exif.subsecond is not None:
        # Subsecond is typically 0-999 milliseconds
        return photo.exif.subsecond / 1000
    
    # No subsecond data available
    return 0.0


def extract_filename_sequence_hint(filename: str) -> int:
    """Extract sequence number from original camera filename.
    
    Looks for numeric suffixes in common camera filename patterns:
    - IMG_001.jpg -> 1
    - DSC_0123.jpg -> 123
    - P1000456.jpg -> 456
    
    Args:
        filename: Original camera filename
        
    Returns:
        Sequence number or 0 if no pattern found
    """
    import re
    
    # Common camera filename patterns
    patterns = [
        r'IMG_(\d+)',      # Canon: IMG_1234.jpg
        r'DSC_(\d+)',      # Nikon: DSC_1234.jpg  
        r'P\d+(\d{3})',    # Panasonic: P1001234.jpg (last 3 digits)
        r'_(\d+)$',        # Generic: prefix_1234.jpg
        r'(\d+)$'          # Generic: prefix1234.jpg
    ]
    
    filename_base = filename.split('.')[0]  # Remove extension
    
    for pattern in patterns:
        match = re.search(pattern, filename_base)
        if match:
            return int(match.group(1))
    
    return 0


def generate_batch_filenames(photos: list[ProcessedPhoto], collection: str = "gallery") -> list[str]:
    """Generate filenames for a batch of photos with proper chronological ordering.
    
    Groups photos by timestamp (to second) + camera, then sorts within each group by:
    1. EXIF timestamp microseconds
    2. EXIF subsecond tag
    3. Original filename sequence hints
    4. Original filename lexical order
    5. Filesystem creation time (path.stat().st_ctime)
    
    Args:
        photos: List of ProcessedPhoto objects
        collection: Collection name for all photos
        
    Returns:
        List of generated filenames in same order as input photos
    """
    from collections import defaultdict
    
    # Group photos by timestamp (to second) + camera
    groups = defaultdict(list)
    
    for i, photo in enumerate(photos):
        # Use collection from photo if available
        collection_name = (photo.collection or collection).lower()
        
        # Get timestamp to the second + camera code for grouping
        timestamp_str = format_iso_timestamp(photo.exif.timestamp or datetime.now())
        camera_code = get_camera_code(photo.camera)
        group_key = f"{collection_name}-{timestamp_str}-{camera_code}"
        
        groups[group_key].append((i, photo))
    
    # Generate filenames for each group
    result_filenames = [''] * len(photos)  # Pre-allocate result array
    
    for group_key, group_photos in groups.items():
        # Sort photos within group by hierarchy
        def sort_key(item):
            _, photo = item
            
            # 1. EXIF subsecond timing (microseconds or subsecond tag)
            subsecond_timing = extract_subsecond_timing(photo)
            
            # 2. Original filename sequence hint
            filename_sequence = extract_filename_sequence_hint(photo.filename)
            
            # 3. Original filename lexical order
            filename_lexical = photo.filename
            
            # 4. Filesystem creation time
            try:
                filesystem_ctime = photo.path.stat().st_ctime
            except:
                filesystem_ctime = 0.0
            
            return (subsecond_timing, filename_sequence, filename_lexical, filesystem_ctime)
        
        # Sort group by the hierarchy
        sorted_group = sorted(group_photos, key=sort_key)
        
        # Assign sequential counters within group
        for counter, (original_index, photo) in enumerate(sorted_group):
            counter_char = LEXICAL_BASE32[counter]
            extension = photo.path.suffix.lower()
            filename = f"{group_key}-{counter_char}{extension}"
            result_filenames[original_index] = filename
    
    return result_filenames


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