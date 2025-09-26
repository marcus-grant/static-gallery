from pathlib import Path
from typing import Union, Optional
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
