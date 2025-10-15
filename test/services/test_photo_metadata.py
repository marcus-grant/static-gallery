from pathlib import Path
from unittest.mock import patch, MagicMock

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