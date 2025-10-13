from src.services.photo_metadata import PhotoMetadataService


def test_photo_metadata_service_scans_prod_pics_directory():
    service = PhotoMetadataService()
    photos = service.scan_processed_photos()
    
    assert len(photos) > 0


def test_photo_metadata_service_extracts_metadata_from_filename():
    """Test that service can parse chronological filename format and extract timestamp, camera, sequence number"""
    service = PhotoMetadataService()
    filename = "wedding-20250809T132034.000Z+0200-r5a-001.jpg"
    metadata = service.extract_metadata_from_filename(filename)
    
    assert metadata["timestamp"] == "20250809T132034.000Z+0200"
    assert metadata["camera"] == "r5a"
    assert metadata["sequence"] == "001"


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
    assert "sequence" in photo