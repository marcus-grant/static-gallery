"""Tests for dual photo collection processing."""
import pytest
from pathlib import Path
from PIL import Image
import piexif

from src.services.file_processing import process_dual_photo_collection
from src.services.s3_storage import calculate_file_checksum
import settings


@pytest.fixture(autouse=True)
def reset_timestamp_offset(monkeypatch):
    """Reset TIMESTAMP_OFFSET_HOURS to 0 for all tests unless explicitly overridden"""
    monkeypatch.setattr(settings, 'TIMESTAMP_OFFSET_HOURS', 0)


class TestProcessDualPhotoCollection:
    """Test process_dual_photo_collection function."""
    
    def test_process_matching_collections(self, tmp_path):
        """Test processing dual collections with matching photos."""
        # Setup directories
        full_dir = tmp_path / "full"
        web_dir = tmp_path / "web"
        output_dir = tmp_path / "output"
        
        full_dir.mkdir()
        web_dir.mkdir()
        
        # Create matching photos with EXIF
        exif_dict = {"0th": {}, "Exif": {}, "1st": {}, "GPS": {}}
        exif_dict["Exif"][piexif.ExifIFD.DateTimeOriginal] = b"2024:10:12 14:30:45"
        exif_bytes = piexif.dump(exif_dict)
        
        # Full resolution
        img_full = Image.new('RGB', (800, 600), color='red')
        img_full.save(full_dir / "IMG_001.jpg", exif=exif_bytes)
        
        # Web version
        img_web = Image.new('RGB', (400, 300), color='red')
        img_web.save(web_dir / "IMG_001.jpg", exif=exif_bytes)
        
        # Process collection
        result = process_dual_photo_collection(
            full_source_dir=full_dir,
            web_source_dir=web_dir,
            output_dir=output_dir,
            collection_name="test"
        )
        
        # Assertions
        assert result["total_processed"] == 1
        assert len(result["errors"]) == 0
        assert len(result["photos"]) == 1
        
        # Check output structure
        assert (output_dir / "full").exists()
        assert (output_dir / "web").exists()
        assert (output_dir / "thumb").exists()
        
        # Check symlinks were created
        full_files = list((output_dir / "full").iterdir())
        web_files = list((output_dir / "web").iterdir())
        thumb_files = list((output_dir / "thumb").iterdir())
        
        assert len(full_files) == 1
        assert len(web_files) == 1
        assert len(thumb_files) == 1
        
        # Check file types
        assert full_files[0].is_symlink()
        assert web_files[0].is_symlink()
        assert thumb_files[0].suffix == ".webp"
    
    def test_skip_processing_when_up_to_date(self, tmp_path):
        """Test that processing is skipped when outputs are up-to-date."""
        # Setup directories and photos (same as first test)
        full_dir = tmp_path / "full"
        web_dir = tmp_path / "web"
        output_dir = tmp_path / "output"
        
        full_dir.mkdir()
        web_dir.mkdir()
        
        # Create matching photos with EXIF
        exif_dict = {"0th": {}, "Exif": {}, "1st": {}, "GPS": {}}
        exif_dict["Exif"][piexif.ExifIFD.DateTimeOriginal] = b"2024:10:12 14:30:45"
        exif_bytes = piexif.dump(exif_dict)
        
        img_full = Image.new('RGB', (800, 600), color='red')
        img_full.save(full_dir / "IMG_001.jpg", exif=exif_bytes)
        
        img_web = Image.new('RGB', (400, 300), color='red')
        img_web.save(web_dir / "IMG_001.jpg", exif=exif_bytes)
        
        # First run - should process everything
        result1 = process_dual_photo_collection(
            full_source_dir=full_dir,
            web_source_dir=web_dir,
            output_dir=output_dir,
            collection_name="test"
        )
        
        assert result1["total_processed"] == 1
        
        # Touch output files to ensure they're newer than source files
        # This simulates the normal case where outputs are up-to-date
        import time
        time.sleep(0.01)  # Small delay to ensure newer timestamps
        
        for output_file in (output_dir / "full").iterdir():
            output_file.touch()
        for output_file in (output_dir / "web").iterdir():
            output_file.touch()
        for output_file in (output_dir / "thumb").iterdir():
            output_file.touch()
        
        # Second run - should skip processing since nothing changed
        result2 = process_dual_photo_collection(
            full_source_dir=full_dir,
            web_source_dir=web_dir,
            output_dir=output_dir,
            collection_name="test"
        )
        
        # Should have skipped processing
        assert result2["total_processed"] == 0
        assert result2["total_skipped"] == 1
    
    def test_timestamp_offset_applied_in_processing(self, tmp_path, monkeypatch):
        """Test that timestamp offset is properly applied during photo processing."""
        # Set timestamp offset to -3 hours
        monkeypatch.setattr(settings, 'TIMESTAMP_OFFSET_HOURS', -3)
        
        # Setup directories
        full_dir = tmp_path / "full"
        web_dir = tmp_path / "web"
        output_dir = tmp_path / "output"
        
        full_dir.mkdir()
        web_dir.mkdir()
        
        # Create matching photos with EXIF timestamp
        exif_dict = {"0th": {}, "Exif": {}, "1st": {}, "GPS": {}}
        exif_dict["Exif"][piexif.ExifIFD.DateTimeOriginal] = b"2024:10:12 14:30:45"
        exif_bytes = piexif.dump(exif_dict)
        
        # Full resolution
        img_full = Image.new('RGB', (800, 600), color='red')
        img_full.save(full_dir / "IMG_001.jpg", exif=exif_bytes)
        
        # Web version
        img_web = Image.new('RGB', (400, 300), color='red')
        img_web.save(web_dir / "IMG_001.jpg", exif=exif_bytes)
        
        # Process collection
        result = process_dual_photo_collection(
            full_source_dir=full_dir,
            web_source_dir=web_dir,
            output_dir=output_dir,
            collection_name="test"
        )
        
        # Verify processing succeeded
        assert result["total_processed"] == 1
        assert len(result["errors"]) == 0
        assert len(result["photos"]) == 1
        
        # Check that the processed photo has the offset applied
        processed_photo = result["photos"][0]
        
        # The timestamp should be offset by -3 hours from original 2024:10:12 14:30:45
        # Original: 2024-10-12 14:30:45
        # With -3 hours: 2024-10-12 11:30:45
        from datetime import datetime
        expected_timestamp = datetime(2024, 10, 12, 11, 30, 45)
        
        # The processed photo should have the offset timestamp
        assert processed_photo.exif.timestamp == expected_timestamp
        
        # The generated filename should reflect the corrected timestamp
        # Format is: test-20241012T113045-unk-0.jpg (YYYYMMDDTHHMMSS)
        assert "20241012T113045" in processed_photo.generated_filename
    
    def test_file_hash_calculation_for_original_files(self, tmp_path):
        """Test that file hashes are calculated for original source files during processing."""
        # Setup directories
        full_dir = tmp_path / "full"
        web_dir = tmp_path / "web"
        output_dir = tmp_path / "output"
        
        full_dir.mkdir()
        web_dir.mkdir()
        
        # Create matching photos with EXIF
        exif_dict = {"0th": {}, "Exif": {}, "1st": {}, "GPS": {}}
        exif_dict["Exif"][piexif.ExifIFD.DateTimeOriginal] = b"2024:06:15 14:30:45"
        exif_bytes = piexif.dump(exif_dict)
        
        # Full resolution
        full_img = Image.new('RGB', (2000, 1500), color='red')
        full_path = full_dir / "IMG_001.jpg"
        full_img.save(full_path, "JPEG", exif=exif_bytes)
        
        # Web optimized  
        web_img = Image.new('RGB', (1200, 900), color='red')
        web_path = web_dir / "IMG_001.jpg"
        web_img.save(web_path, "JPEG", exif=exif_bytes)
        
        # Calculate expected hash of original full file
        expected_hash = calculate_file_checksum(full_path)
        
        # Process the collection
        result = process_dual_photo_collection(
            full_source_dir=full_dir,
            web_source_dir=web_dir,
            output_dir=output_dir,
            collection_name="test"
        )
        
        # Verify processing succeeded
        assert result["total_processed"] == 1
        assert len(result["photos"]) == 1
        
        # Check that the processed photo has original file hash
        processed_photo = result["photos"][0]
        assert hasattr(processed_photo, 'file_hash')
        assert processed_photo.file_hash == expected_hash
        
        # Verify hash is SHA256 format
        assert len(processed_photo.file_hash) == 64  # SHA256 hex length
        assert all(c in '0123456789abcdef' for c in processed_photo.file_hash)
    
    def test_generate_gallery_metadata_json(self, tmp_path, monkeypatch):
        """Test that gallery-metadata.json is generated during photo processing."""
        # Set timestamp offset for testing
        monkeypatch.setattr(settings, 'TIMESTAMP_OFFSET_HOURS', -4)
        
        # Setup directories
        full_dir = tmp_path / "full"
        web_dir = tmp_path / "web"
        output_dir = tmp_path / "output"
        
        full_dir.mkdir()
        web_dir.mkdir()
        
        # Create matching photos with EXIF
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
        
        # Process the collection
        result = process_dual_photo_collection(
            full_source_dir=full_dir,
            web_source_dir=web_dir,
            output_dir=output_dir,
            collection_name="wedding"
        )
        
        # Verify processing succeeded
        assert result["total_processed"] == 1
        
        # Check that gallery-metadata.json was created
        metadata_file = output_dir / "gallery-metadata.json"
        assert metadata_file.exists()
        
        # Parse and verify metadata content
        import json
        with open(metadata_file) as f:
            metadata = json.load(f)
        
        # Verify schema structure
        assert metadata["schema_version"] == "1.0"
        assert metadata["collection"] == "wedding"
        assert "generated_at" in metadata
        assert metadata["settings"]["timestamp_offset_hours"] == -4
        assert len(metadata["photos"]) == 1
        
        # Verify photo metadata
        photo_meta = metadata["photos"][0]
        assert photo_meta["original_path"] == str(full_path)
        assert "file_hash" in photo_meta
        assert photo_meta["exif"]["original_timestamp"] == "2024-08-10T18:30:45"
        assert photo_meta["exif"]["corrected_timestamp"] == "2024-08-10T14:30:45"  # -4 hours
        assert photo_meta["exif"]["timezone_original"] == "+00:00"
        
        # Verify file paths
        processed_photo = result["photos"][0]
        expected_filename = processed_photo.generated_filename
        assert photo_meta["files"]["full"] == f"full/{expected_filename}"
        assert photo_meta["files"]["web"] == f"web/{expected_filename}"
        assert photo_meta["files"]["thumb"] == expected_filename.replace(".jpg", ".webp")