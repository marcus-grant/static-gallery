"""Photo data models."""

from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any


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
    collection: Optional[str] = None
    generated_filename: Optional[str] = None
    file_hash: Optional[str] = None


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
        collection=None,
        generated_filename=None,
    )


@dataclass
class MetadataExifData:
    """EXIF data structure for gallery metadata."""
    
    original_timestamp: Optional[str]
    corrected_timestamp: Optional[str]
    timezone_original: str
    camera: Dict[str, Optional[str]]
    subsecond: Optional[int]


@dataclass
class MetadataFileData:
    """File paths structure for gallery metadata."""
    
    full: str
    web: str
    thumb: str


@dataclass
class PhotoMetadata:
    """Individual photo metadata for gallery JSON."""
    
    id: str
    original_path: str
    file_hash: str
    deployment_file_hash: str
    exif: MetadataExifData
    files: MetadataFileData


@dataclass
class GallerySettings:
    """Settings structure for gallery metadata."""
    
    timestamp_offset_hours: int = 0
    target_timezone_offset_hours: int = 13  # 13 = preserve original timezone
    web_size: tuple = (2048, 2048)
    thumb_size: tuple = (400, 400)
    jpeg_quality: int = 85
    webp_quality: int = 85


@dataclass
class GalleryMetadata:
    """Complete gallery metadata structure."""
    
    schema_version: str
    generated_at: str
    collection: str
    settings: GallerySettings
    photos: List[PhotoMetadata]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GalleryMetadata':
        """Create from dictionary (JSON deserialization)."""
        settings = GallerySettings(**data["settings"])
        photos = [
            PhotoMetadata(
                id=p["id"],
                original_path=p["original_path"],
                file_hash=p["file_hash"],
                deployment_file_hash=p["deployment_file_hash"],
                exif=MetadataExifData(**p["exif"]),
                files=MetadataFileData(**p["files"])
            )
            for p in data["photos"]
        ]
        
        return cls(
            schema_version=data["schema_version"],
            generated_at=data["generated_at"],
            collection=data["collection"],
            settings=settings,
            photos=photos
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
        collection=data.get("collection"),
        generated_filename=data.get("generated_filename"),
        file_hash=data.get("file_hash"),
    )

