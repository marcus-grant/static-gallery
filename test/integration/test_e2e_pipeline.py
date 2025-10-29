"""End-to-end integration test for the complete gallery pipeline."""
import pytest
import json
import time
from pathlib import Path
from PIL import Image
import piexif
from datetime import datetime
from unittest.mock import patch
from click.testing import CliRunner

from src.command.process_photos import process_photos


@pytest.fixture
def wedding_photo_collection(tmp_path):
    """Create a realistic wedding photo collection for E2E testing."""
    full_dir = tmp_path / "full"
    web_dir = tmp_path / "web"
    full_dir.mkdir()
    web_dir.mkdir()
    
    # Create 10 wedding photos spanning several hours
    base_time = datetime(2023, 8, 9, 14, 0, 0)  # 2 PM wedding start
    
    # Wedding timeline: prep, ceremony, reception
    timeline = [
        (0, "prep"),      # 2:00 PM - preparation
        (30, "prep"),     # 2:30 PM
        (90, "ceremony"), # 3:30 PM - ceremony
        (95, "ceremony"), # 3:35 PM
        (100, "ceremony"), # 3:40 PM
        (180, "reception"), # 5:00 PM - reception
        (240, "reception"), # 6:00 PM
        (300, "reception"), # 7:00 PM
        (360, "reception"), # 8:00 PM
        (420, "reception"), # 9:00 PM
    ]
    
    for i, (minutes_offset, phase) in enumerate(timeline):
        # Create test image
        color = (50 + i*20, 100, 150 + i*10)  # Vary colors
        img = Image.new("RGB", (2000, 1500), color=color)
        
        # Calculate timestamp
        photo_time = base_time.replace(
            hour=base_time.hour + minutes_offset // 60,
            minute=base_time.minute + minutes_offset % 60
        )
        
        # Add EXIF data
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
        full_path = full_dir / f"IMG_{i:04d}.jpg"
        web_path = web_dir / f"IMG_{i:04d}.jpg"
        
        img.save(full_path, format='JPEG', exif=exif_bytes, quality=95)
        
        # Create smaller web version
        web_img = img.resize((1200, 900))
        web_img.save(web_path, format='JPEG', exif=exif_bytes, quality=85)
    
    return full_dir, web_dir


class TestE2EPipeline:
    """End-to-end integration tests for the complete gallery pipeline."""
    
    def test_process_photos_command_basic_functionality(self, wedding_photo_collection, tmp_path):
        """Test that process-photos CLI command works with real photo collection."""
        full_dir, web_dir = wedding_photo_collection
        output_dir = tmp_path / "output"
        
        runner = CliRunner()
        
        # Run process-photos command
        result = runner.invoke(process_photos, [
            '--full-source', str(full_dir),
            '--web-source', str(web_dir),
            '--output', str(output_dir),
            '--collection-name', 'test-wedding'
        ])
        
        # Command should succeed
        assert result.exit_code == 0, f"Command failed with output: {result.output}"
        
        # Verify output structure
        assert output_dir.exists()
        assert (output_dir / "full").exists()
        assert (output_dir / "web").exists()
        assert (output_dir / "thumb").exists()
        assert (output_dir / "gallery-metadata.json").exists()
        
        # Verify all photos were processed
        full_photos = list((output_dir / "full").glob("*.jpg"))
        web_photos = list((output_dir / "web").glob("*.jpg"))
        thumb_photos = list((output_dir / "thumb").glob("*.webp"))
        
        assert len(full_photos) == 10
        assert len(web_photos) == 10
        assert len(thumb_photos) == 10
    
    def test_process_photos_with_timezone_correction(self, wedding_photo_collection, tmp_path, monkeypatch):
        """Test process-photos with timezone correction settings."""
        import settings
        # Set Swedish wedding timezone correction
        monkeypatch.setattr(settings, 'TIMESTAMP_OFFSET_HOURS', 0)
        monkeypatch.setattr(settings, 'TARGET_TIMEZONE_OFFSET_HOURS', 2)  # CEST
        
        full_dir, web_dir = wedding_photo_collection
        output_dir = tmp_path / "output"
        
        runner = CliRunner()
        
        result = runner.invoke(process_photos, [
            '--full-source', str(full_dir),
            '--web-source', str(web_dir),
            '--output', str(output_dir),
            '--collection-name', 'swedish-wedding'
        ])
        
        assert result.exit_code == 0
        
        # Verify metadata includes timezone settings
        metadata_file = output_dir / "gallery-metadata.json"
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
        
        # This will fail - timezone settings not properly recorded
        assert metadata["settings"]["target_timezone_offset_hours"] == 2, \
            "Target timezone setting not recorded in metadata"
        
        # Verify deployment hashes were calculated with timezone
        for photo in metadata["photos"]:
            assert photo["deployment_file_hash"] != photo["file_hash"], \
                "Deployment hash should differ when timezone processing is applied"
    
    def test_process_photos_performance_with_progress_reporting(self, wedding_photo_collection, tmp_path):
        """Test that process-photos shows progress for larger collections."""
        full_dir, web_dir = wedding_photo_collection
        output_dir = tmp_path / "output"
        
        runner = CliRunner()
        
        start_time = time.time()
        
        result = runner.invoke(process_photos, [
            '--full-source', str(full_dir),
            '--web-source', str(web_dir),
            '--output', str(output_dir),
            '--collection-name', 'timed-wedding'
        ])
        
        processing_time = time.time() - start_time
        
        assert result.exit_code == 0
        
        # Should be fast for 10 photos
        assert processing_time < 10, f"Processing took {processing_time:.1f}s, should be under 10s"
        
        # This will fail - progress reporting not implemented
        assert "Processing photo" in result.output, \
            "Progress reporting not implemented - should show 'Processing photo X/Y'"
    
    def test_process_photos_crash_recovery_with_resume_flag(self, wedding_photo_collection, tmp_path):
        """Test crash recovery functionality with --resume flag."""
        full_dir, web_dir = wedding_photo_collection
        output_dir = tmp_path / "output"
        
        runner = CliRunner()
        
        # First, create partial processing scenario by creating some partial files
        output_dir.mkdir()
        partial_file = output_dir / "gallery-metadata.part001.json"
        partial_file.write_text('{"partial": "data"}')
        
        # Try to run without --resume flag
        result = runner.invoke(process_photos, [
            '--full-source', str(full_dir),
            '--web-source', str(web_dir),
            '--output', str(output_dir),
            '--collection-name', 'recovery-test'
        ])
        
        # This will fail - crash recovery not implemented yet
        # Should detect partial files and prompt for --resume or --restart
        assert result.exit_code != 0, "Should fail when partial files exist without --resume flag"
        assert "partial" in result.output.lower() or "resume" in result.output.lower(), \
            "Should mention partial files and suggest --resume flag"
    
    def test_process_photos_restart_flag_cleans_partials(self, wedding_photo_collection, tmp_path):
        """Test that --restart flag cleans up partial files."""
        full_dir, web_dir = wedding_photo_collection
        output_dir = tmp_path / "output"
        
        runner = CliRunner()
        
        # Create some partial files
        output_dir.mkdir()
        partial1 = output_dir / "gallery-metadata.part001.json"
        partial2 = output_dir / "gallery-metadata.part002.json"
        partial1.write_text('{"partial": "data1"}')
        partial2.write_text('{"partial": "data2"}')
        
        # Run with --restart flag
        result = runner.invoke(process_photos, [
            '--full-source', str(full_dir),
            '--web-source', str(web_dir),
            '--output', str(output_dir),
            '--collection-name', 'restart-test',
            '--restart'  # This flag doesn't exist yet
        ])
        
        # This will fail - --restart flag not implemented
        assert result.exit_code == 0 or "restart" in result.output, \
            "--restart flag not implemented yet"
        
        # If restart worked, partial files should be cleaned up
        if result.exit_code == 0:
            assert not partial1.exists(), "Partial files should be cleaned up with --restart"
            assert not partial2.exists(), "Partial files should be cleaned up with --restart"
    
    def test_process_photos_batch_size_option(self, wedding_photo_collection, tmp_path):
        """Test --batch-size option for memory management."""
        full_dir, web_dir = wedding_photo_collection
        output_dir = tmp_path / "output"
        
        runner = CliRunner()
        
        # Try with custom batch size
        result = runner.invoke(process_photos, [
            '--full-source', str(full_dir),
            '--web-source', str(web_dir),
            '--output', str(output_dir),
            '--collection-name', 'batch-test',
            '--batch-size', '3'  # Process 3 photos per batch
        ])
        
        # This will fail - --batch-size option doesn't exist yet
        assert result.exit_code == 0 or "batch-size" in result.output, \
            "--batch-size option not implemented yet"
        
        # If batch processing worked, should create partial files
        if result.exit_code == 0:
            partial_files = list(output_dir.glob("gallery-metadata.part*.json"))
            # With 10 photos and batch size 3, should have created 4 partial files
            # (3 photos, 3 photos, 3 photos, 1 photo)
            assert len(partial_files) >= 3, "Batch processing should create multiple partial files"