"""Tests for data models."""

import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path



class TestCameraInfo:
    """Test CameraInfo dataclass."""
    
    def test_camera_info_creation(self):
        """Test creating CameraInfo with make and model."""
        from src.models.photo import CameraInfo
        
        camera = CameraInfo(make="Canon", model="EOS 5D")
        assert camera.make == "Canon"
        assert camera.model == "EOS 5D"
    
    def test_camera_info_none_values(self):
        """Test CameraInfo with None values."""
        from src.models.photo import CameraInfo
        
        camera = CameraInfo(make=None, model=None)
        assert camera.make is None
        assert camera.model is None
    
    def test_camera_info_to_dict(self):
        """Test converting CameraInfo to dict for JSON."""
        from src.models.photo import CameraInfo
        
        camera = CameraInfo(make="Nikon", model="D850")
        camera_dict = asdict(camera)
        
        assert camera_dict == {"make": "Nikon", "model": "D850"}
        # Ensure it's JSON serializable
        json_str = json.dumps(camera_dict)
        assert "Nikon" in json_str


class TestExifData:
    """Test ExifData dataclass."""
    
    def test_exif_data_creation(self):
        """Test creating ExifData with all fields."""
        from src.models.photo import ExifData
        
        timestamp = datetime(2024, 10, 5, 14, 30, 45)
        exif = ExifData(
            timestamp=timestamp,
            subsecond=123,
            gps_latitude=40.7128,
            gps_longitude=-74.0060,
            raw_data={"EXIF DateTimeOriginal": "2024:10:05 14:30:45"}
        )
        
        assert exif.timestamp == timestamp
        assert exif.subsecond == 123
        assert exif.gps_latitude == 40.7128
        assert exif.gps_longitude == -74.0060
        assert "EXIF DateTimeOriginal" in exif.raw_data
    
    def test_exif_data_optional_fields(self):
        """Test ExifData with None values."""
        from src.models.photo import ExifData
        
        exif = ExifData(
            timestamp=None,
            subsecond=None,
            gps_latitude=None,
            gps_longitude=None,
            raw_data={}
        )
        
        assert exif.timestamp is None
        assert exif.subsecond is None
        assert exif.gps_latitude is None
        assert exif.gps_longitude is None
        assert exif.raw_data == {}
    
    def test_exif_data_to_dict(self):
        """Test converting ExifData to dict with datetime handling."""
        from src.models.photo import ExifData
        
        timestamp = datetime(2024, 10, 5, 14, 30, 45)
        exif = ExifData(
            timestamp=timestamp,
            subsecond=456,
            gps_latitude=None,
            gps_longitude=None,
            raw_data={"Image Make": "Canon"}
        )
        
        exif_dict = asdict(exif)
        assert exif_dict["timestamp"] == timestamp  # datetime object
        assert exif_dict["subsecond"] == 456
        
        # For JSON serialization, we need to handle datetime
        exif_dict["timestamp"] = exif_dict["timestamp"].isoformat() if exif_dict["timestamp"] else None
        json_str = json.dumps(exif_dict)
        assert "2024-10-05T14:30:45" in json_str


class TestProcessedPhoto:
    """Test ProcessedPhoto dataclass."""
    
    def test_processed_photo_creation(self):
        """Test creating complete ProcessedPhoto."""
        from src.models.photo import ProcessedPhoto, CameraInfo, ExifData
        
        camera = CameraInfo(make="Canon", model="EOS R5")
        exif = ExifData(
            timestamp=datetime(2024, 10, 5, 12, 0, 0),
            subsecond=None,
            gps_latitude=None,
            gps_longitude=None,
            raw_data={}
        )
        
        photo = ProcessedPhoto(
            path=Path("/pics/IMG_001.jpg"),
            filename="IMG_001.jpg",
            file_size=2048576,
            camera=camera,
            exif=exif,
            edge_cases=["burst"]
        )
        
        assert photo.path == Path("/pics/IMG_001.jpg")
        assert photo.filename == "IMG_001.jpg"
        assert photo.file_size == 2048576
        assert photo.camera.make == "Canon"
        assert photo.exif.timestamp == datetime(2024, 10, 5, 12, 0, 0)
        assert "burst" in photo.edge_cases
    
    def test_processed_photo_with_collection(self):
        """Test ProcessedPhoto with collection field."""
        from src.models.photo import ProcessedPhoto, CameraInfo, ExifData
        
        camera = CameraInfo(make=None, model=None)
        exif = ExifData(timestamp=None, subsecond=None, 
                       gps_latitude=None, gps_longitude=None, raw_data={})
        
        photo = ProcessedPhoto(
            path=Path("/pics/photo.jpg"),
            filename="photo.jpg",
            file_size=1024,
            camera=camera,
            exif=exif,
            edge_cases=[],
            collection="wedding"
        )
        
        assert photo.collection == "wedding"
    
    def test_processed_photo_to_dict(self):
        """Test converting ProcessedPhoto to dict for JSON."""
        from src.models.photo import ProcessedPhoto, CameraInfo, ExifData
        
        camera = CameraInfo(make="Sony", model="A7III")
        exif = ExifData(
            timestamp=datetime(2024, 10, 5, 10, 0, 0),
            subsecond=100,
            gps_latitude=40.0,
            gps_longitude=-74.0,
            raw_data={"key": "value"}
        )
        
        photo = ProcessedPhoto(
            path=Path("/home/user/pics/photo.jpg"),
            filename="photo.jpg",
            file_size=3145728,
            camera=camera,
            exif=exif,
            edge_cases=["missing_exif", "burst"]
        )
        
        photo_dict = asdict(photo)
        
        # Check nested dataclass conversion
        assert photo_dict["camera"]["make"] == "Sony"
        assert photo_dict["exif"]["subsecond"] == 100
        assert len(photo_dict["edge_cases"]) == 2
        
        # Path needs string conversion for JSON
        photo_dict["path"] = str(photo_dict["path"])
        photo_dict["exif"]["timestamp"] = photo_dict["exif"]["timestamp"].isoformat() if photo_dict["exif"]["timestamp"] else None
        
        # Ensure JSON serializable
        json_str = json.dumps(photo_dict)
        assert "/home/user/pics/photo.jpg" in json_str
        assert "Sony" in json_str


class TestModelHelpers:
    """Test helper functions for model operations."""
    
    def test_photo_from_exif_service_data(self):
        """Test creating ProcessedPhoto from exif service output."""
        from src.models.photo import ProcessedPhoto, photo_from_exif_service
        
        # Simulate exif service data structure
        photo_path = Path("/pics/IMG_123.jpg")
        exif_data = {
            "EXIF DateTimeOriginal": "2024:10:05 14:30:45",
            "Image Make": "Canon",
            "Image Model": "EOS 5D"
        }
        camera_info = {"make": "Canon", "model": "EOS 5D"}
        timestamp = datetime(2024, 10, 5, 14, 30, 45)
        
        photo = photo_from_exif_service(
            path=photo_path,
            timestamp=timestamp,
            camera_info=camera_info,
            exif_data=exif_data,
            subsecond=None,
            edge_cases=[]
        )
        
        assert isinstance(photo, ProcessedPhoto)
        assert photo.path == photo_path
        assert photo.filename == "IMG_123.jpg"
        assert photo.camera.make == "Canon"
        assert photo.exif.timestamp == timestamp
        assert photo.exif.raw_data == exif_data
    
    def test_json_serialization_helpers(self):
        """Test JSON serialization helper functions."""
        from src.models.photo import ProcessedPhoto, CameraInfo, ExifData
        from src.models.photo import photo_to_json, photo_from_json
        
        # Create a photo
        photo = ProcessedPhoto(
            path=Path("/pics/test.jpg"),
            filename="test.jpg",
            file_size=1024,
            camera=CameraInfo(make="Test", model="Camera"),
            exif=ExifData(
                timestamp=datetime(2024, 10, 5, 12, 0, 0),
                subsecond=None,
                gps_latitude=None,
                gps_longitude=None,
                raw_data={}
            ),
            edge_cases=["test"]
        )
        
        # Convert to JSON
        json_data = photo_to_json(photo)
        assert isinstance(json_data, dict)
        assert json_data["path"] == "/pics/test.jpg"
        assert json_data["exif"]["timestamp"] == "2024-10-05T12:00:00"
        
        # Convert back from JSON
        restored_photo = photo_from_json(json_data)
        assert isinstance(restored_photo, ProcessedPhoto)
        assert restored_photo.path == Path("/pics/test.jpg")
        assert restored_photo.camera.make == "Test"
        assert restored_photo.exif.timestamp == datetime(2024, 10, 5, 12, 0, 0)


class TestPhotoMetadata:
    """Test PhotoMetadata dataclass for gallery JSON metadata."""
    
    def test_photo_metadata_creation_with_dual_hashes(self):
        """Test creating PhotoMetadata with both original and deployment file hashes."""
        from src.models.photo import PhotoMetadata, MetadataExifData, MetadataFileData
        
        exif_data = MetadataExifData(
            original_timestamp="2024-08-10T18:30:45",
            corrected_timestamp="2024-08-10T14:30:45",
            timezone_original="+00:00",
            camera={"make": "Canon", "model": "EOS R5"},
            subsecond=None
        )
        
        files_data = MetadataFileData(
            full="full/wedding-20240810T143045-r5a-0.jpg",
            web="web/wedding-20240810T143045-r5a-0.jpg", 
            thumb="wedding-20240810T143045-r5a-0.webp"
        )
        
        photo_meta = PhotoMetadata(
            id="wedding-20240810T143045-r5a-0",
            original_path="/path/to/IMG_001.jpg",
            file_hash="abc123original",
            deployment_file_hash="def456deployment",
            exif=exif_data,
            files=files_data
        )
        
        assert photo_meta.file_hash == "abc123original"
        assert photo_meta.deployment_file_hash == "def456deployment"
        assert photo_meta.id == "wedding-20240810T143045-r5a-0"
    
    def test_photo_metadata_serialization_with_dual_hashes(self):
        """Test that PhotoMetadata with dual hashes serializes correctly."""
        from src.models.photo import PhotoMetadata, MetadataExifData, MetadataFileData
        
        exif_data = MetadataExifData(
            original_timestamp="2024-08-10T18:30:45",
            corrected_timestamp="2024-08-10T14:30:45", 
            timezone_original="+00:00",
            camera={"make": "Canon", "model": "EOS R5"},
            subsecond=None
        )
        
        files_data = MetadataFileData(
            full="full/test.jpg",
            web="web/test.jpg",
            thumb="test.webp"
        )
        
        photo_meta = PhotoMetadata(
            id="test-photo",
            original_path="/original/test.jpg",
            file_hash="original_hash_123",
            deployment_file_hash="deploy_hash_456",
            exif=exif_data,
            files=files_data
        )
        
        # Convert to dict for JSON serialization
        meta_dict = asdict(photo_meta)
        
        assert meta_dict["file_hash"] == "original_hash_123"
        assert meta_dict["deployment_file_hash"] == "deploy_hash_456"
        assert "exif" in meta_dict
        assert "files" in meta_dict
        
        # Ensure it's JSON serializable
        json_str = json.dumps(meta_dict)
        assert "original_hash_123" in json_str
        assert "deploy_hash_456" in json_str
    
    def test_gallery_metadata_with_dual_hash_photos(self):
        """Test that GalleryMetadata handles photos with dual hashes correctly."""
        from src.models.photo import (
            GalleryMetadata, GallerySettings, PhotoMetadata, 
            MetadataExifData, MetadataFileData
        )
        
        settings = GallerySettings(timestamp_offset_hours=-4)
        
        photo_meta = PhotoMetadata(
            id="test-photo-1",
            original_path="/src/IMG_001.jpg",
            file_hash="hash_original_001",
            deployment_file_hash="hash_deploy_001",
            exif=MetadataExifData(
                original_timestamp="2024-08-10T18:30:45",
                corrected_timestamp="2024-08-10T14:30:45",
                timezone_original="+00:00",
                camera={"make": "Canon", "model": "EOS R5"},
                subsecond=None
            ),
            files=MetadataFileData(
                full="full/test-001.jpg",
                web="web/test-001.jpg",
                thumb="test-001.webp"
            )
        )
        
        gallery_meta = GalleryMetadata(
            schema_version="1.0",
            generated_at="2025-10-28T10:00:00Z",
            collection="test-collection",
            settings=settings,
            photos=[photo_meta]
        )
        
        # Test to_dict method includes dual hashes
        meta_dict = gallery_meta.to_dict()
        photo_dict = meta_dict["photos"][0]
        
        assert photo_dict["file_hash"] == "hash_original_001"
        assert photo_dict["deployment_file_hash"] == "hash_deploy_001"
        
        # Test from_dict method preserves dual hashes
        restored_meta = GalleryMetadata.from_dict(meta_dict)
        restored_photo = restored_meta.photos[0]
        
        assert restored_photo.file_hash == "hash_original_001"
        assert restored_photo.deployment_file_hash == "hash_deploy_001"