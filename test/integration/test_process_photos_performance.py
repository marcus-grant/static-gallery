"""Integration test for process-photos performance and memory management."""
import pytest
import time
from pathlib import Path
from PIL import Image
import piexif
from datetime import datetime

from src.services.file_processing import process_dual_photo_collection


@pytest.fixture
def large_photo_collection(tmp_path):
    """Create a collection of 50 photos to test memory management and performance."""
    full_dir = tmp_path / "full"
    web_dir = tmp_path / "web" 
    full_dir.mkdir()
    web_dir.mkdir()
    
    # Create 50 test photos with EXIF data
    photos = []
    for i in range(50):
        # Create test image
        img = Image.new("RGB", (4000, 3000), color=(i*5, 100, 150))  # Large image to test memory
        
        # Add EXIF data with sequential timestamps
        base_time = datetime(2023, 8, 9, 14, 0, 0)
        photo_time = base_time.replace(minute=base_time.minute + i)
        
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
        
        # Create smaller web version
        web_img = img.resize((2048, 1536))
        web_img.save(web_path, format='JPEG', exif=exif_bytes, quality=85)
        
        photos.append((full_path, web_path))
    
    return full_dir, web_dir, photos


class TestProcessPhotosPerformance:
    """Integration tests for process-photos performance and memory management."""
    
    def test_process_large_collection_performance(self, large_photo_collection, tmp_path):
        """Test that processing large collection completes in reasonable time."""
        full_dir, web_dir, photos = large_photo_collection
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        
        # Process the collection
        start_time = time.time()
        
        result = process_dual_photo_collection(
            full_source_dir=full_dir,
            web_source_dir=web_dir,
            output_dir=output_dir,
            collection_name="test-collection"
        )
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Performance requirements - should be fast with batch processing
        assert processing_time < 30, f"Processing took {processing_time:.1f}s, should be under 30s for 50 photos"
        
        # Verify all photos were processed
        assert result is not None
        assert len(result["photos"]) == 50
        
        # Verify metadata file was created
        metadata_file = output_dir / "gallery-metadata.json"
        assert metadata_file.exists()
    
    def test_process_photos_with_progress_reporting(self, large_photo_collection, tmp_path, capsys):
        """Test that progress is reported during processing (when implemented)."""
        full_dir, web_dir, photos = large_photo_collection
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        
        # Process collection and capture output
        result = process_dual_photo_collection(
            full_source_dir=full_dir,
            web_source_dir=web_dir,
            output_dir=output_dir,
            collection_name="test-collection"
        )
        
        captured = capsys.readouterr()
        
        # This test will initially fail - progress reporting not implemented yet
        # Once implemented, should show progress like "Processing photo 25/50"
        assert "Processing photo" in captured.out or "Processing photo" in captured.err, \
            "Progress reporting not implemented yet"
    
    def test_batch_processing_creates_partial_files(self, large_photo_collection, tmp_path):
        """Test that batch processing creates partial files for crash recovery."""
        full_dir, web_dir, photos = large_photo_collection
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        
        # Process collection
        result = process_dual_photo_collection(
            full_source_dir=full_dir,
            web_source_dir=web_dir,
            output_dir=output_dir,
            collection_name="test-collection"
        )
        
        # This test will initially fail - batch processing not implemented yet
        # Should find partial files like gallery-metadata.part001.json
        partial_files = list(output_dir.glob("gallery-metadata.part*.json"))
        
        # For now, expect this to fail since batch processing isn't implemented
        assert len(partial_files) > 0, "Batch processing with partial files not implemented yet"
    
    def test_deployment_hash_calculation_works(self, large_photo_collection, tmp_path):
        """Test that deployment hash calculation works for all photos."""
        full_dir, web_dir, photos = large_photo_collection
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        
        result = process_dual_photo_collection(
            full_source_dir=full_dir,
            web_source_dir=web_dir,
            output_dir=output_dir,
            collection_name="test-collection"
        )
        
        # Check that deployment hashes were calculated by reading the metadata file
        assert result is not None
        
        # Read the generated metadata file to check deployment hashes
        import json
        metadata_file = output_dir / "gallery-metadata.json"
        assert metadata_file.exists()
        
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
        
        # Check that deployment hashes were calculated in metadata
        assert "photos" in metadata
        for photo in metadata["photos"]:
            assert "deployment_file_hash" in photo
            assert photo["deployment_file_hash"] != ""
            assert photo["deployment_file_hash"] != photo["file_hash"], \
                "Deployment hash should differ from file hash when timezone processing applied"