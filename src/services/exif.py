from pathlib import Path
from typing import Union, Optional, List, Tuple, Dict
from datetime import datetime, timedelta
import exifread
import re
import settings


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
            dt = datetime.strptime(datetime_str, "%Y:%m:%d %H:%M:%S")
            
            # Apply timestamp offset if configured
            if hasattr(settings, 'TIMESTAMP_OFFSET_HOURS') and settings.TIMESTAMP_OFFSET_HOURS != 0:
                dt = dt + timedelta(hours=settings.TIMESTAMP_OFFSET_HOURS)
            
            return dt
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
    
    # Sort by timestamp, then by camera (make+model), then by filename sequence
    # Create sort key that handles None values in camera info
    def sort_key(item):
        path, dt, cam = item
        camera_key = (
            cam.get("make") or "",
            cam.get("model") or ""
        )
        # Use numeric filename sequence instead of alphabetical filename
        filename_sequence = extract_filename_sequence(path)
        return (dt, camera_key, filename_sequence, path.name)
    
    with_timestamps.sort(key=sort_key)
    
    # For photos without timestamps, sort by camera then filename sequence
    def sort_key_no_timestamp(item):
        path, _, cam = item
        camera_key = (
            cam.get("make") or "",
            cam.get("model") or ""
        )
        # Use numeric filename sequence instead of alphabetical filename
        filename_sequence = extract_filename_sequence(path)
        return (camera_key, filename_sequence, path.name)
    
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
    current_camera = None
    
    for i, (photo_path, timestamp, camera_info) in enumerate(sorted_photos):
        # Skip photos without timestamps
        if timestamp is None:
            continue
            
        # Get camera identifier
        camera_key = (camera_info.get("make"), camera_info.get("model"))
            
        if not current_burst:
            # Start a new burst
            current_burst = [photo_path]
            current_camera = camera_key
        else:
            # Check if this photo is part of the current burst
            # Must be same camera AND within time interval
            last_photo = current_burst[-1]
            same_camera = camera_key == current_camera
            
            if same_camera and is_burst_candidate(last_photo, photo_path, max_interval_ms):
                # Add to current burst
                current_burst.append(photo_path)
            else:
                # End current burst if it has multiple photos
                if len(current_burst) > 1:
                    burst_sequences.append(current_burst)
                # Start new burst with this photo
                current_burst = [photo_path]
                current_camera = camera_key
    
    # Don't forget the last burst
    if len(current_burst) > 1:
        burst_sequences.append(current_burst)
    
    return burst_sequences


def find_timestamp_conflicts(photos: List[Union[Path, str]]) -> List[List[Path]]:
    """Find photos with same timestamp from different cameras.
    Args:
        photos: List of photo file paths
    Returns:
        List of conflict groups, each containing paths with same timestamp
    """
    # Group photos by timestamp
    timestamp_groups = {}
    
    for photo in photos:
        photo_path = Path(photo)
        dt = get_datetime_taken(photo_path)
        
        if dt is None:
            continue
            
        # Add subsecond precision if available
        subsec = get_subsecond_precision(photo_path)
        if subsec is not None:
            dt = combine_datetime_subsecond(dt, subsec)
        
        # Convert to string for grouping
        timestamp_key = dt.isoformat()
        
        if timestamp_key not in timestamp_groups:
            timestamp_groups[timestamp_key] = []
        timestamp_groups[timestamp_key].append(photo_path)
    
    # Find groups with multiple photos from different cameras
    conflict_groups = []
    
    for timestamp, group_photos in timestamp_groups.items():
        if len(group_photos) < 2:
            continue
            
        # Check if photos are from different cameras
        cameras = set()
        for photo_path in group_photos:
            camera_info = get_camera_info(photo_path)
            camera_key = (camera_info.get("make"), camera_info.get("model"))
            cameras.add(camera_key)
        
        # If we have multiple different cameras, it's a conflict
        if len(cameras) > 1:
            conflict_groups.append(group_photos)
    
    return conflict_groups


def find_missing_exif_photos(photos: List[Union[Path, str]]) -> List[Path]:
    """Find photos without critical EXIF data.
    Args:
        photos: List of photo file paths
    Returns:
        List of paths to photos missing critical EXIF data (timestamp)
    """
    missing_exif = []
    
    for photo in photos:
        photo_path = Path(photo)
        
        # Check if photo has timestamp (critical EXIF data)
        dt = get_datetime_taken(photo_path)
        
        if dt is None:
            missing_exif.append(photo_path)
    
    return missing_exif


def get_camera_diversity_samples(
    photos: List[Union[Path, str]]
) -> Dict[Tuple[Optional[str], Optional[str]], List[Path]]:
    """Group photos by camera make/model for diversity testing.
    Args:
        photos: List of photo file paths
    Returns:
        Dict mapping (make, model) tuples to lists of photo paths
    """
    camera_groups = {}
    
    for photo in photos:
        photo_path = Path(photo)
        camera_info = get_camera_info(photo_path)
        
        # Create camera key (make, model)
        camera_key = (camera_info.get("make"), camera_info.get("model"))
        
        if camera_key not in camera_groups:
            camera_groups[camera_key] = []
        
        camera_groups[camera_key].append(photo_path)
    
    return camera_groups


def extract_filename_sequence(filename: Union[Path, str]) -> int:
    """Extract sequence number from camera filename.
    
    Supports common camera filename patterns:
    - Canon: 4F6A5096.JPG -> 5096
    - Canon: 5W9A2423.JPG -> 2423  
    - Generic: IMG_1234.JPG -> 1234
    - Generic: DSC_5678.JPG -> 5678
    
    Args:
        filename: Photo filename or path
    Returns:
        Sequence number as integer, 0 if pattern not recognized
    """
    if isinstance(filename, Path):
        filename = filename.name
    
    # Remove extension
    name_without_ext = filename.rsplit('.', 1)[0]
    
    # Canon pattern: 4-char prefix + 4-digit number (e.g., 4F6A5096, 5W9A2423)
    canon_match = re.match(r'^[A-Z0-9]{4}(\d{4})$', name_without_ext)
    if canon_match:
        return int(canon_match.group(1))
    
    # IMG pattern: IMG_nnnn (e.g., IMG_1234)
    img_match = re.match(r'^IMG_(\d+)$', name_without_ext, re.IGNORECASE)
    if img_match:
        return int(img_match.group(1))
    
    # DSC pattern: DSC_nnnn (e.g., DSC_5678)
    dsc_match = re.match(r'^DSC_(\d+)$', name_without_ext, re.IGNORECASE)
    if dsc_match:
        return int(dsc_match.group(1))
    
    # If no pattern matches, return 0
    return 0


def get_timezone_info(photo_path: Union[Path, str]) -> Optional[str]:
    """Extract timezone offset information from photo EXIF data.
    
    Args:
        photo_path: Path to the photo file
        
    Returns:
        Timezone offset string (e.g., "+02:00", "-05:00") if found, None otherwise
    """
    photo_path = Path(photo_path)
    try:
        with open(photo_path, "rb") as f:
            tags = exifread.process_file(f, stop_tag="EXIF OffsetTimeDigitized")
        
        # Check for timezone offset tags in order of preference
        timezone_tags = [
            "EXIF OffsetTimeOriginal",    # Preferred - when photo was taken
            "EXIF OffsetTimeDigitized",   # Fallback - when photo was digitized
        ]
        
        for tag_name in timezone_tags:
            if tag_name in tags:
                timezone_str = str(tags[tag_name])
                # Validate format (should be like "+02:00" or "-05:00")
                if re.match(r'^[+-]\d{2}:\d{2}$', timezone_str):
                    return timezone_str
                    
        return None
        
    except Exception:
        return None
