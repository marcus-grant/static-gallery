from pathlib import Path
from typing import Union, Optional, List, Tuple
from datetime import datetime
import exifread


def get_datetime_taken(photo_path: Union[Path, str]) -> Optional[datetime]:
    """Extract datetime taken from photo EXIF data.
    Args:
        photo_path: Path to the photo file
    Returns:
        datetime object if DateTimeOriginal found, None otherwise
    """
    photo_path = Path(photo_path)
    try:
        with open(photo_path, "rb") as f:
            tags = exifread.process_file(f, stop_tag="EXIF DateTimeOriginal")
        if "EXIF DateTimeOriginal" in tags:
            datetime_str = str(tags["EXIF DateTimeOriginal"])
            # Parse EXIF datetime format: "YYYY:MM:DD HH:MM:SS"
            return datetime.strptime(datetime_str, "%Y:%m:%d %H:%M:%S")
    except (FileNotFoundError, OSError):
        pass
    return None


def get_subsecond_precision(photo_path: Union[Path, str]) -> Optional[int]:
    """Extract subsecond precision from photo EXIF data.
    Args:
        photo_path: Path to the photo file
    Returns:
        Integer representing subsecond precision (milliseconds), None if not found
    """
    photo_path = Path(photo_path)
    try:
        with open(photo_path, "rb") as f:
            tags = exifread.process_file(f, stop_tag="EXIF SubSecTimeOriginal")

        if "EXIF SubSecTimeOriginal" in tags:
            subsec_str = str(tags["EXIF SubSecTimeOriginal"])
            try:
                return int(subsec_str)
            except ValueError:
                pass
    except (FileNotFoundError, OSError):
        pass
    return None


def get_camera_info(photo_path: Union[Path, str]) -> dict:
    """Extract camera make and model from photo EXIF data.
    Args:
        photo_path: Path to the photo file
    Returns:
        Dictionary with 'make' and 'model' keys, values can be None
    """
    photo_path = Path(photo_path)
    try:
        with open(photo_path, "rb") as f:
            tags = exifread.process_file(f, details=False)
        make = None
        model = None
        if "Image Make" in tags:
            make = str(tags["Image Make"]).strip()
        if "Image Model" in tags:
            model = str(tags["Image Model"]).strip()
        return {"make": make, "model": model}
    except (FileNotFoundError, OSError):
        return {"make": None, "model": None}


def extract_exif_data(photo_path: Union[Path, str]) -> dict:
    """Extract all EXIF data from a photo file.
    Args:
        photo_path: Path to the photo file
    Returns:
        Dictionary of all EXIF tags and their values
    """
    photo_path = Path(photo_path)
    try:
        with open(photo_path, "rb") as f:
            tags = exifread.process_file(f)
        # Convert tags to a simple dictionary
        result = {}
        for tag, value in tags.items():
            # Skip some internal tags
            if tag not in (
                "JPEGThumbnail",
                "TIFFThumbnail",
                "Filename",
                "EXIF MakerNote",
            ):
                result[tag] = str(value)
        return result
    except (FileNotFoundError, OSError):
        return {}


def combine_datetime_subsecond(
    dt: datetime, subsec: Optional[Union[int, str]]
) -> datetime:
    """Combine datetime with subsecond precision for accurate sorting.
    Args:
        dt: Base datetime object
        subsec: Subsecond value (milliseconds), can be int or string
    Returns:
        datetime object with microseconds set from subsecond value
    """
    if subsec is None:
        return dt
    
    # Convert to string and handle different precisions
    subsec_str = str(subsec)
    
    # Pad with zeros on the right to get microseconds
    # 1 digit = 100ms precision -> 100000 microseconds
    # 2 digits = 10ms precision -> 10000 microseconds  
    # 3 digits = 1ms precision -> 1000 microseconds
    if len(subsec_str) == 1:
        microseconds = int(subsec_str) * 100000
    elif len(subsec_str) == 2:
        microseconds = int(subsec_str) * 10000
    else:  # 3+ digits
        microseconds = int(subsec_str[:3]) * 1000
    
    return dt.replace(microsecond=microseconds)


def has_subsecond_precision(photo_path: Union[Path, str]) -> bool:
    """Check if camera supports subsecond timestamps.
    Args:
        photo_path: Path to the photo file
    Returns:
        True if photo has SubSecTimeOriginal EXIF tag, False otherwise
    """
    subsec = get_subsecond_precision(photo_path)
    return subsec is not None


def sort_photos_chronologically(
    photos: List[Union[Path, str]]
) -> List[Tuple[Path, datetime, dict]]:
    """Sort photos by timestamp + camera/filename fallback for identical times.
    Args:
        photos: List of photo file paths
    Returns:
        List of tuples (Path, datetime, camera_info) sorted chronologically
    """
    # Extract timestamps and camera info for all photos
    photo_data = []
    for photo in photos:
        photo_path = Path(photo)
        dt = get_datetime_taken(photo_path)
        camera_info = get_camera_info(photo_path)
        
        if dt is not None:
            # Check if has subsecond precision
            subsec = get_subsecond_precision(photo_path)
            if subsec is not None:
                dt = combine_datetime_subsecond(dt, subsec)
            
            photo_data.append((photo_path, dt, camera_info))
        else:
            # No EXIF timestamp - these will be handled separately
            photo_data.append((photo_path, None, camera_info))
    
    # Separate photos with and without timestamps
    with_timestamps = [(p, dt, cam) for p, dt, cam in photo_data if dt is not None]
    without_timestamps = [(p, dt, cam) for p, dt, cam in photo_data if dt is None]
    
    # Sort by timestamp, then by camera (make+model), then by filename
    # Create sort key that handles None values in camera info
    def sort_key(item):
        path, dt, cam = item
        camera_key = (
            cam.get("make") or "",
            cam.get("model") or ""
        )
        return (dt, camera_key, path.name)
    
    with_timestamps.sort(key=sort_key)
    
    # For photos without timestamps, sort by camera then filename
    def sort_key_no_timestamp(item):
        path, _, cam = item
        camera_key = (
            cam.get("make") or "",
            cam.get("model") or ""
        )
        return (camera_key, path.name)
    
    without_timestamps.sort(key=sort_key_no_timestamp)
    
    # Return with timestamp photos first, then without
    return with_timestamps + without_timestamps


def is_burst_candidate(
    photo1: Union[Path, str], photo2: Union[Path, str], max_interval_ms: int = 200
) -> bool:
    """Check if two photos are part of same burst sequence.
    Args:
        photo1: Path to first photo
        photo2: Path to second photo  
        max_interval_ms: Maximum milliseconds between photos to consider burst
    Returns:
        True if photos are within burst interval, False otherwise
    """
    photo1_path = Path(photo1)
    photo2_path = Path(photo2)
    
    # Get timestamps for both photos
    dt1 = get_datetime_taken(photo1_path)
    dt2 = get_datetime_taken(photo2_path)
    
    # Both must have timestamps
    if dt1 is None or dt2 is None:
        return False
    
    # Add subsecond precision if available
    subsec1 = get_subsecond_precision(photo1_path)
    subsec2 = get_subsecond_precision(photo2_path)
    
    if subsec1 is not None:
        dt1 = combine_datetime_subsecond(dt1, subsec1)
    if subsec2 is not None:
        dt2 = combine_datetime_subsecond(dt2, subsec2)
    
    # Calculate time difference in milliseconds
    time_diff = abs((dt2 - dt1).total_seconds() * 1000)
    
    return time_diff <= max_interval_ms


def detect_burst_sequences(
    sorted_photos: List[Tuple[Path, datetime, dict]], max_interval_ms: int = 200
) -> List[List[Path]]:
    """Group photos taken in rapid succession (within ~200ms).
    Args:
        sorted_photos: List of tuples from sort_photos_chronologically
        max_interval_ms: Maximum milliseconds between photos to consider burst
    Returns:
        List of burst sequences, each containing paths of burst photos
    """
    if not sorted_photos:
        return []
    
    burst_sequences = []
    current_burst = []
    
    for i, (photo_path, timestamp, camera_info) in enumerate(sorted_photos):
        # Skip photos without timestamps
        if timestamp is None:
            continue
            
        if not current_burst:
            # Start a new burst
            current_burst = [photo_path]
        else:
            # Check if this photo is part of the current burst
            # Compare with the last photo in current burst
            last_photo = current_burst[-1]
            
            if is_burst_candidate(last_photo, photo_path, max_interval_ms):
                # Add to current burst
                current_burst.append(photo_path)
            else:
                # End current burst if it has multiple photos
                if len(current_burst) > 1:
                    burst_sequences.append(current_burst)
                # Start new burst with this photo
                current_burst = [photo_path]
    
    # Don't forget the last burst
    if len(current_burst) > 1:
        burst_sequences.append(current_burst)
    
    return burst_sequences
