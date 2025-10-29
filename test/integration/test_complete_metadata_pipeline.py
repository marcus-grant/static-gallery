"""Integration test for complete metadata recording in gallery pipeline."""
import pytest
import json
from pathlib import Path
from PIL import Image
import piexif
from datetime import datetime

from src.services.file_processing import process_dual_photo_collection


@pytest.fixture
def sample_photo_collection(tmp_path):
    """Create a small collection of photos to test metadata recording."""
    full_dir = tmp_path / "full"
    web_dir = tmp_path / "web"
    full_dir.mkdir()
    web_dir.mkdir()
    
    # Create 3 test photos with EXIF data
    for i in range(3):
        # Create test image
        img = Image.new("RGB", (1000, 800), color=(i*50, 100, 200))
        
        # Add EXIF data with sequential timestamps
        base_time = datetime(2023, 8, 9, 14, 0, 0)
        photo_time = base_time.replace(minute=base_time.minute + i*10)
        
        exif_dict = {
            "0th": {
                piexif.ImageIFD.Make: b"Canon",
                piexif.ImageIFD.Model: b"EOS R5"
            },
            "Exif": {
                piexif.ExifIFD.DateTimeOriginal: photo_time.strftime("%Y:%m:%d %H:%M:%S").encode()
            },
            "1st": {},
            "GPS": {},
        }
        
        exif_bytes = piexif.dump(exif_dict)
        
        # Save full and web versions
        full_path = full_dir / f"IMG_{i:03d}.jpg"
        web_path = web_dir / f"IMG_{i:03d}.jpg"
        
        img.save(full_path, format='JPEG', exif=exif_bytes, quality=95)
        img.save(web_path, format='JPEG', exif=exif_bytes, quality=85)
    
    return full_dir, web_dir


class TestCompleteMetadataPipeline:
    """Integration tests for complete metadata recording."""
    
    def test_gallery_metadata_includes_all_processing_settings(self, sample_photo_collection, tmp_path):
        """Test that gallery metadata includes all processing settings used."""
        full_dir, web_dir = sample_photo_collection
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        
        # Process collection
        result = process_dual_photo_collection(
            full_source_dir=full_dir,
            web_source_dir=web_dir,
            output_dir=output_dir,
            collection_name="test-collection"
        )
        
        # Read the generated metadata file
        metadata_file = output_dir / "gallery-metadata.json"
        assert metadata_file.exists()
        
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
        
        # Verify basic structure
        assert "settings" in metadata
        settings = metadata["settings"]
        
        # Critical settings that should be recorded for deployment comparison
        assert "timestamp_offset_hours" in settings, "timestamp_offset_hours missing from metadata"
        
        # This test will fail - target_timezone_offset_hours not recorded yet
        assert "target_timezone_offset_hours" in settings, \
            "target_timezone_offset_hours missing from metadata - needed for deployment comparison"
        
        # Photo processing settings should also be recorded
        assert "web_size" in settings, "web_size missing from metadata"
        assert "thumb_size" in settings, "thumb_size missing from metadata"
        assert "jpeg_quality" in settings, "jpeg_quality missing from metadata"
        assert "webp_quality" in settings, "webp_quality missing from metadata"
    
    def test_photo_metadata_includes_deployment_hashes(self, sample_photo_collection, tmp_path, monkeypatch):
        """Test that each photo has both file_hash and deployment_file_hash."""
        # Set timezone to ensure deployment hash differs from file hash
        import settings
        monkeypatch.setattr(settings, 'TARGET_TIMEZONE_OFFSET_HOURS', 2)
        
        full_dir, web_dir = sample_photo_collection
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        
        # Process collection
        result = process_dual_photo_collection(
            full_source_dir=full_dir,
            web_source_dir=web_dir,
            output_dir=output_dir,
            collection_name="test-collection"
        )
        
        # Read the generated metadata file
        metadata_file = output_dir / "gallery-metadata.json"
        assert metadata_file.exists()
        
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
        
        # Verify all photos have dual hashes
        assert "photos" in metadata
        photos = metadata["photos"]
        assert len(photos) == 3
        
        for photo in photos:
            assert "file_hash" in photo, "file_hash missing from photo metadata"
            assert "deployment_file_hash" in photo, "deployment_file_hash missing from photo metadata"
            
            # Both hashes should be present and non-empty
            assert photo["file_hash"] != "", "file_hash should not be empty"
            assert photo["deployment_file_hash"] != "", "deployment_file_hash should not be empty"
            
            # When timezone is set, deployment hash should differ from file hash
            assert photo["deployment_file_hash"] != photo["file_hash"], \
                "deployment_file_hash should differ from file_hash when timezone processing is applied"
    
    def test_metadata_timezone_settings_affect_deployment_hashes(self, sample_photo_collection, tmp_path, monkeypatch):
        """Test that changing timezone settings results in different deployment hashes."""
        import settings
        
        full_dir, web_dir = sample_photo_collection
        output_dir1 = tmp_path / "output1"
        output_dir2 = tmp_path / "output2"
        output_dir1.mkdir()
        output_dir2.mkdir()
        
        # Process with timezone -5 (EST)
        monkeypatch.setattr(settings, 'TARGET_TIMEZONE_OFFSET_HOURS', -5)
        result1 = process_dual_photo_collection(
            full_source_dir=full_dir,
            web_source_dir=web_dir,
            output_dir=output_dir1,
            collection_name="test-collection"
        )
        
        # Process with timezone +2 (CET)
        monkeypatch.setattr(settings, 'TARGET_TIMEZONE_OFFSET_HOURS', 2)
        result2 = process_dual_photo_collection(
            full_source_dir=full_dir,
            web_source_dir=web_dir,
            output_dir=output_dir2,
            collection_name="test-collection"
        )
        
        # Read both metadata files
        with open(output_dir1 / "gallery-metadata.json", 'r') as f:
            metadata1 = json.load(f)
        
        with open(output_dir2 / "gallery-metadata.json", 'r') as f:
            metadata2 = json.load(f)
        
        # Settings should be recorded and different
        assert metadata1["settings"]["target_timezone_offset_hours"] == -5
        assert metadata2["settings"]["target_timezone_offset_hours"] == 2
        
        # Deployment hashes should be different for same photos with different timezone settings
        photos1 = metadata1["photos"]
        photos2 = metadata2["photos"]
        
        for i in range(len(photos1)):
            photo1 = photos1[i]
            photo2 = photos2[i]
            
            # File hashes should be the same (same source files)
            assert photo1["file_hash"] == photo2["file_hash"]
            
            # Deployment hashes should be different (different timezone processing)
            assert photo1["deployment_file_hash"] != photo2["deployment_file_hash"], \
                f"Deployment hashes should differ when timezone settings change"
    
    def test_metadata_records_processing_environment(self, sample_photo_collection, tmp_path):
        """Test that metadata includes information about processing environment."""
        full_dir, web_dir = sample_photo_collection
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        
        # Process collection
        result = process_dual_photo_collection(
            full_source_dir=full_dir,
            web_source_dir=web_dir,
            output_dir=output_dir,
            collection_name="test-collection"
        )
        
        # Read the generated metadata file
        metadata_file = output_dir / "gallery-metadata.json"
        assert metadata_file.exists()
        
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
        
        # Should include processing metadata
        assert "schema_version" in metadata
        assert "generated_at" in metadata
        assert "collection" in metadata
        assert metadata["collection"] == "test-collection"
        
        # Should include generation timestamp
        generated_at = metadata["generated_at"]
        assert generated_at != ""
        
        # Should be a valid ISO timestamp
        try:
            datetime.fromisoformat(generated_at.replace('Z', '+00:00'))
        except ValueError:
            pytest.fail(f"generated_at '{generated_at}' is not a valid ISO timestamp")