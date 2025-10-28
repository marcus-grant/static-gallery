"""Integration test for dual-hash system with EXIF modification."""
import pytest
from pathlib import Path
from datetime import datetime
import settings
from PIL import Image
import piexif

from src.services.file_processing import generate_gallery_metadata
from src.models.photo import ProcessedPhoto, CameraInfo, ExifData


@pytest.fixture(autouse=True)
def reset_settings(monkeypatch):
    """Reset settings for each test."""
    monkeypatch.setattr(settings, 'TIMESTAMP_OFFSET_HOURS', 0)
    monkeypatch.setattr(settings, 'TARGET_TIMEZONE_OFFSET_HOURS', 13)


@pytest.fixture
def sample_photo_with_exif(tmp_path):
    """Create a sample photo with EXIF data."""
    # Create test image with EXIF
    img = Image.new("RGB", (100, 100), color="blue")
    
    exif_dict = {
        "0th": {
            piexif.ImageIFD.Make: b"Canon",
            piexif.ImageIFD.Model: b"EOS R5"
        },
        "Exif": {
            piexif.ExifIFD.DateTimeOriginal: b"2023:12:25 15:30:45"
        },
        "1st": {},
        "GPS": {},
    }
    
    exif_bytes = piexif.dump(exif_dict)
    
    photo_path = tmp_path / "test_photo.jpg"
    img.save(photo_path, format='JPEG', exif=exif_bytes)
    
    return photo_path


def create_processed_photo(photo_path):
    """Create a ProcessedPhoto object from a photo path."""
    timestamp = datetime(2023, 12, 25, 15, 30, 45)
    
    return ProcessedPhoto(
        path=photo_path,
        filename=photo_path.name,
        file_size=photo_path.stat().st_size,
        camera=CameraInfo(make="Canon", model="EOS R5"),
        exif=ExifData(
            timestamp=timestamp,
            subsecond=None,
            gps_latitude=None,
            gps_longitude=None,
            raw_data={}
        ),
        edge_cases=[],
        collection="test-collection",
        generated_filename="20231225-153045-000.jpg",
        file_hash="original_file_hash_123"
    )


class TestDualHashIntegration:
    """Test dual-hash system integration with EXIF modification."""
    
    def test_deployment_hash_differs_from_file_hash_when_timezone_set(self, sample_photo_with_exif, monkeypatch):
        """Test that deployment hash differs from file hash when timezone is set."""
        # Set target timezone (not preserve original)
        monkeypatch.setattr(settings, 'TARGET_TIMEZONE_OFFSET_HOURS', -5)
        
        photo = create_processed_photo(sample_photo_with_exif)
        
        metadata = generate_gallery_metadata([photo], "test-collection")
        photo_meta = metadata.photos[0]
        
        # Deployment hash should be different from file hash when timezone is modified
        assert photo_meta.file_hash == "original_file_hash_123"
        assert photo_meta.deployment_file_hash != "original_file_hash_123"
        assert photo_meta.deployment_file_hash != ""
    
    def test_deployment_hash_changes_with_different_timezone_settings(self, sample_photo_with_exif, monkeypatch):
        """Test that deployment hash changes when timezone settings change."""
        photo = create_processed_photo(sample_photo_with_exif)
        
        # Generate metadata with timezone -5
        monkeypatch.setattr(settings, 'TARGET_TIMEZONE_OFFSET_HOURS', -5)
        metadata_est = generate_gallery_metadata([photo], "test-collection")
        hash_est = metadata_est.photos[0].deployment_file_hash
        
        # Generate metadata with timezone +2
        monkeypatch.setattr(settings, 'TARGET_TIMEZONE_OFFSET_HOURS', 2)
        metadata_cet = generate_gallery_metadata([photo], "test-collection")
        hash_cet = metadata_cet.photos[0].deployment_file_hash
        
        # Generate metadata with preserve original (13)
        monkeypatch.setattr(settings, 'TARGET_TIMEZONE_OFFSET_HOURS', 13)
        metadata_preserve = generate_gallery_metadata([photo], "test-collection")
        hash_preserve = metadata_preserve.photos[0].deployment_file_hash
        
        # All hashes should be different
        assert hash_est != hash_cet
        assert hash_est != hash_preserve
        assert hash_cet != hash_preserve
    
    def test_deployment_hash_preserves_original_when_offset_13(self, sample_photo_with_exif, monkeypatch):
        """Test that deployment hash handling when preserving original timezone."""
        # Set to preserve original timezone
        monkeypatch.setattr(settings, 'TARGET_TIMEZONE_OFFSET_HOURS', 13)
        
        photo = create_processed_photo(sample_photo_with_exif)
        
        metadata = generate_gallery_metadata([photo], "test-collection")
        photo_meta = metadata.photos[0]
        
        # With preserve original (13), deployment hash should still be calculated
        # but will reflect the "preserve original timezone" modification
        assert photo_meta.deployment_file_hash != ""
        assert photo_meta.file_hash == "original_file_hash_123"
    
    def test_deployment_hash_consistent_for_same_settings(self, sample_photo_with_exif, monkeypatch):
        """Test that deployment hash is consistent for same settings."""
        monkeypatch.setattr(settings, 'TARGET_TIMEZONE_OFFSET_HOURS', -5)
        
        photo = create_processed_photo(sample_photo_with_exif)
        
        # Generate metadata twice with same settings
        metadata1 = generate_gallery_metadata([photo], "test-collection")
        metadata2 = generate_gallery_metadata([photo], "test-collection")
        
        hash1 = metadata1.photos[0].deployment_file_hash
        hash2 = metadata2.photos[0].deployment_file_hash
        
        # Hashes should be identical for same settings
        assert hash1 == hash2
        assert hash1 != ""
    
    def test_deployment_hash_falls_back_to_original_on_error(self, tmp_path, monkeypatch):
        """Test that deployment hash falls back to original hash on EXIF modification error."""
        monkeypatch.setattr(settings, 'TARGET_TIMEZONE_OFFSET_HOURS', -5)
        
        # Create a non-image file
        bad_file = tmp_path / "not_an_image.jpg"
        bad_file.write_text("This is not an image")
        
        photo = create_processed_photo(bad_file)
        
        metadata = generate_gallery_metadata([photo], "test-collection")
        photo_meta = metadata.photos[0]
        
        # Should fall back to original hash when EXIF modification fails
        assert photo_meta.deployment_file_hash == "original_file_hash_123"