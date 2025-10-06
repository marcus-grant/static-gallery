"""Photo data models."""

from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict
import json


@dataclass
class CameraInfo:
    """Camera make and model information."""

    make: Optional[str]
    model: Optional[str]


@dataclass
class ExifData:
    """EXIF metadata from photo."""

    timestamp: Optional[datetime]
    subsecond: Optional[int]
    gps_latitude: Optional[float]
    gps_longitude: Optional[float]
    raw_data: Dict[str, str]  # Full EXIF dict


@dataclass
class ProcessedPhoto:
    """Complete photo metadata record."""

    path: Path
    filename: str
    file_size: int
    camera: CameraInfo
    exif: ExifData
    edge_cases: List[str]
    uuid: Optional[str] = None


def photo_from_exif_service(
    path: Path,
    timestamp: Optional[datetime],
    camera_info: dict,
    exif_data: dict,
    subsecond: Optional[int],
    edge_cases: List[str],
) -> ProcessedPhoto:
    """Create ProcessedPhoto from exif service output."""
    camera = CameraInfo(make=camera_info.get("make"), model=camera_info.get("model"))

    exif = ExifData(
        timestamp=timestamp,
        subsecond=subsecond,
        gps_latitude=None,  # TODO: Extract GPS from exif_data
        gps_longitude=None,
        raw_data=exif_data,
    )

    return ProcessedPhoto(
        path=path,
        filename=path.name,
        file_size=path.stat().st_size if path.exists() else 0,
        camera=camera,
        exif=exif,
        edge_cases=edge_cases,
        uuid=None,
    )


def photo_to_json(photo: ProcessedPhoto) -> dict:
    """Convert ProcessedPhoto to JSON-serializable dict."""
    data = asdict(photo)
    # Convert Path to string
    data["path"] = str(data["path"])
    # Convert datetime to ISO format
    if data["exif"]["timestamp"]:
        data["exif"]["timestamp"] = data["exif"]["timestamp"].isoformat()
    return data


def photo_from_json(data: dict) -> ProcessedPhoto:
    """Create ProcessedPhoto from JSON dict."""
    # Convert path string back to Path
    data["path"] = Path(data["path"])

    # Convert timestamp string back to datetime
    if data["exif"]["timestamp"]:
        data["exif"]["timestamp"] = datetime.fromisoformat(data["exif"]["timestamp"])

    # Create nested dataclasses
    camera = CameraInfo(**data["camera"])
    exif = ExifData(**data["exif"])

    return ProcessedPhoto(
        path=data["path"],
        filename=data["filename"],
        file_size=data["file_size"],
        camera=camera,
        exif=exif,
        edge_cases=data["edge_cases"],
        uuid=data.get("uuid"),
    )

