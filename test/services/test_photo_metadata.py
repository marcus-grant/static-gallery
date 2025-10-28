from pathlib import Path
from unittest.mock import patch, MagicMock
import json

from src.services.photo_metadata import PhotoMetadataService


def test_photo_metadata_service_scans_prod_pics_directory():
    service = PhotoMetadataService()
    photos = service.scan_processed_photos()
    
    assert len(photos) > 0


def test_photo_metadata_service_extracts_metadata_from_filename():
    """Test that service can parse chronological filename format and extract timestamp, camera, counter"""
    service = PhotoMetadataService()
    # Format matches what filename_service generates: collection-YYYYMMDDTHHMMSS-camera-counter.jpg
    filename = "wedding-20250809T132034-r5a-0.jpg"
    metadata = service.extract_metadata_from_filename(filename)
    
    assert metadata["collection"] == "wedding"
    assert metadata["timestamp"] == "20250809T132034"
    assert metadata["camera"] == "r5a"
    assert metadata["counter"] == "0"


def test_photo_metadata_service_generates_json_structure():
    """Test that service generates JSON structure with photo metadata for frontend consumption"""
    service = PhotoMetadataService()
    json_data = service.generate_json_metadata()
    
    assert "photos" in json_data
    assert len(json_data["photos"]) > 0
    
    photo = json_data["photos"][0]
    assert "filename" in photo
    assert "timestamp" in photo
    assert "camera" in photo
    assert "counter" in photo


def test_photo_metadata_service_returns_photos_in_chronological_order():
    """Test that photos are returned sorted by filename (which encodes chronological order)"""
    service = PhotoMetadataService()
    
    # Mock the glob to return photos in non-chronological order
    mock_photos = [
        MagicMock(name="wedding-20250809T140817-r5a-0.jpg"),
        MagicMock(name="wedding-20250809T132034-r5a-0.jpg"),  # Earlier time
        MagicMock(name="wedding-20250809T134458-r5a-0.jpg"),  # Middle time
        MagicMock(name="wedding-20250809T140817-r5a-1.jpg"),  # Same time, different counter
    ]
    for mock in mock_photos:
        mock.name = mock._mock_name
    
    with patch("pathlib.Path.glob") as mock_glob:
        mock_glob.return_value = mock_photos
        photos = service.scan_processed_photos()
    
    # Should be sorted chronologically
    assert len(photos) == 4
    assert photos[0].name == "wedding-20250809T132034-r5a-0.jpg"
    assert photos[1].name == "wedding-20250809T134458-r5a-0.jpg"
    assert photos[2].name == "wedding-20250809T140817-r5a-0.jpg"
    assert photos[3].name == "wedding-20250809T140817-r5a-1.jpg"


def test_photo_metadata_service_reads_from_json_metadata(tmp_path):
    """Test that service can read metadata from gallery-metadata.json instead of parsing filenames"""
    # Create test gallery metadata JSON
    metadata = {
        "schema_version": "1.0",
        "generated_at": "2024-10-28T12:00:00Z",
        "collection": "wedding", 
        "settings": {"timestamp_offset_hours": -4},
        "photos": [
            {
                "id": "wedding-20240810T143045-r5a-0",
                "original_path": "pics-full/IMG_001.jpg",
                "file_hash": "abc123def456",
                "exif": {
                    "original_timestamp": "2024-08-10T18:30:45",
                    "corrected_timestamp": "2024-08-10T14:30:45", 
                    "timezone_original": "+00:00",
                    "camera": {"make": "Canon", "model": "EOS R5"},
                    "subsecond": 123
                },
                "files": {
                    "full": "full/wedding-20240810T143045-r5a-0.jpg",
                    "web": "web/wedding-20240810T143045-r5a-0.jpg",
                    "thumb": "wedding-20240810T143045-r5a-0.webp"
                }
            },
            {
                "id": "wedding-20240810T144500-r5a-0",
                "original_path": "pics-full/IMG_002.jpg",
                "file_hash": "def456ghi789",
                "exif": {
                    "original_timestamp": "2024-08-10T18:45:00",
                    "corrected_timestamp": "2024-08-10T14:45:00",
                    "timezone_original": "+00:00", 
                    "camera": {"make": "Canon", "model": "EOS R5"},
                    "subsecond": None
                },
                "files": {
                    "full": "full/wedding-20240810T144500-r5a-0.jpg",
                    "web": "web/wedding-20240810T144500-r5a-0.jpg",
                    "thumb": "wedding-20240810T144500-r5a-0.webp"
                }
            }
        ]
    }
    
    # Save metadata JSON to temp directory
    prod_dir = tmp_path / "prod"
    prod_dir.mkdir()
    metadata_file = prod_dir / "gallery-metadata.json"
    with open(metadata_file, 'w') as f:
        json.dump(metadata, f)
    
    # Test service reading from JSON
    service = PhotoMetadataService()
    json_data = service.generate_json_metadata_from_file(str(metadata_file))
    
    # Verify JSON structure
    assert "photos" in json_data
    assert len(json_data["photos"]) == 2
    
    # Verify first photo data
    photo1 = json_data["photos"][0]
    assert photo1["id"] == "wedding-20240810T143045-r5a-0"
    assert photo1["timestamp"] == "2024-08-10T14:30:45"
    assert photo1["camera"] == "Canon EOS R5"
    assert photo1["full_url"] == "photos/full/wedding-20240810T143045-r5a-0.jpg"
    assert photo1["web_url"] == "photos/web/wedding-20240810T143045-r5a-0.jpg"
    assert photo1["thumb_url"] == "photos/thumb/wedding-20240810T143045-r5a-0.webp"
    
    # Verify second photo data  
    photo2 = json_data["photos"][1]
    assert photo2["id"] == "wedding-20240810T144500-r5a-0"
    assert photo2["timestamp"] == "2024-08-10T14:45:00"


def test_integration_photo_processing_to_metadata_service(tmp_path):
    """Integration test: process photos -> generate metadata -> read metadata"""
    from src.services.file_processing import process_dual_photo_collection
    from PIL import Image
    import piexif
    
    # Setup directories
    full_dir = tmp_path / "full"
    web_dir = tmp_path / "web"
    output_dir = tmp_path / "output"
    
    full_dir.mkdir()
    web_dir.mkdir()
    
    # Create test photos with EXIF
    exif_dict = {"0th": {}, "Exif": {}, "1st": {}, "GPS": {}}
    exif_dict["Exif"][piexif.ExifIFD.DateTimeOriginal] = b"2024:08:10 18:30:45"
    exif_bytes = piexif.dump(exif_dict)
    
    # Full resolution
    full_img = Image.new('RGB', (2000, 1500), color='red')
    full_path = full_dir / "IMG_001.jpg"
    full_img.save(full_path, "JPEG", exif=exif_bytes)
    
    # Web optimized
    web_img = Image.new('RGB', (1200, 900), color='red') 
    web_path = web_dir / "IMG_001.jpg"
    web_img.save(web_path, "JPEG", exif=exif_bytes)
    
    # Step 1: Process photos (generates gallery-metadata.json)
    result = process_dual_photo_collection(
        full_source_dir=full_dir,
        web_source_dir=web_dir,
        output_dir=output_dir,
        collection_name="test"
    )
    
    assert result["total_processed"] == 1
    
    # Step 2: Verify metadata file was created
    metadata_file = output_dir / "gallery-metadata.json"
    assert metadata_file.exists()
    
    # Step 3: Use PhotoMetadataService to read the metadata
    service = PhotoMetadataService()
    json_data = service.generate_json_metadata_from_file(str(metadata_file))
    
    # Step 4: Verify the complete round-trip works
    assert "photos" in json_data
    assert len(json_data["photos"]) == 1
    
    photo = json_data["photos"][0]
    processed_photo = result["photos"][0]
    
    # Verify ID matches generated filename
    expected_id = processed_photo.generated_filename.replace('.jpg', '')
    assert photo["id"] == expected_id
    
    # Verify timestamp matches processed photo
    assert photo["timestamp"] == processed_photo.exif.timestamp.isoformat()
    
    # Verify URLs are properly formatted
    assert photo["full_url"] == f"photos/full/{processed_photo.generated_filename}"
    assert photo["web_url"] == f"photos/web/{processed_photo.generated_filename}"
    assert photo["thumb_url"] == f"photos/thumb/{processed_photo.generated_filename.replace('.jpg', '.webp')}"