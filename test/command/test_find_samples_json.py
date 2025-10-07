"""Test find-samples command JSON output functionality."""

import json

import pytest
from click.testing import CliRunner

from src.command.find_samples import find_samples
import settings


class TestFindSamplesJSON:
    """Test JSON output functionality of find-samples command."""
    
    def test_save_to_default_cache_file(self, tmp_path, monkeypatch, create_test_images):
        """Test saving results to default cache file location."""
        # Create test images
        test_dir = tmp_path / "photos"
        test_dir.mkdir()
        create_test_images(test_dir, count=3)
        
        # Mock cache directory
        cache_dir = tmp_path / "cache"
        cache_dir.mkdir()
        monkeypatch.setattr(settings, 'CACHE_DIR', cache_dir)
        
        runner = CliRunner()
        result = runner.invoke(find_samples, [
            '-s', str(test_dir),
            '--save-json'
        ])
        
        if result.exit_code != 0:
            print(f"Command failed with output:\n{result.output}")
        assert result.exit_code == 0
        assert "Saved photo metadata to" in result.output
        
        # Check JSON file was created
        json_file = cache_dir / "photos.json"
        assert json_file.exists()
        
        # Verify JSON content
        with open(json_file) as f:
            data = json.load(f)
        
        assert "photos" in data
        assert len(data["photos"]) == 3
        assert "summary" in data
        assert data["summary"]["total_photos"] == 3
    
    def test_save_to_custom_cache_file(self, tmp_path, create_test_images):
        """Test saving results to custom cache file location."""
        test_dir = tmp_path / "photos"
        test_dir.mkdir()
        create_test_images(test_dir, count=2)
        
        custom_json = tmp_path / "custom_photos.json"
        
        runner = CliRunner()
        result = runner.invoke(find_samples, [
            '-s', str(test_dir),
            '--save-json',
            '--cache-file', str(custom_json)
        ])
        
        assert result.exit_code == 0
        assert custom_json.exists()
        
        with open(custom_json) as f:
            data = json.load(f)
        assert len(data["photos"]) == 2
    
    def test_json_structure_with_edge_cases(self, tmp_path, create_test_images_with_exif):
        """Test JSON structure includes all photo metadata and edge cases."""
        test_dir = tmp_path / "photos"
        test_dir.mkdir()
        
        # Create photos with different edge cases
        create_test_images_with_exif(test_dir, [
            {"filename": "IMG_001.jpg", "timestamp": "2024:10:05 12:00:00", "make": "Canon", "model": "EOS R5"},
            {"filename": "IMG_002.jpg", "timestamp": "2024:10:05 12:00:00", "make": "Canon", "model": "EOS R5"},  # Same timestamp
            {"filename": "IMG_003.jpg", "timestamp": None, "make": None, "model": None},  # Missing EXIF
        ])
        
        json_file = tmp_path / "test_output.json"
        
        runner = CliRunner()
        result = runner.invoke(find_samples, [
            '-s', str(test_dir),
            '--save-json',
            '--cache-file', str(json_file)
        ])
        
        assert result.exit_code == 0
        
        with open(json_file) as f:
            data = json.load(f)
        
        # Check photo structure
        photos = data["photos"]
        assert len(photos) == 3
        
        # Verify photo fields
        photo = photos[0]
        assert "path" in photo
        assert "filename" in photo
        assert "file_size" in photo
        assert "camera" in photo
        assert "exif" in photo
        assert "edge_cases" in photo
        assert "collection" in photo  # Should be None for now
        
        # Check summary includes edge case counts
        summary = data["summary"]
        assert "edge_case_counts" in summary
        assert "cameras" in summary
    
    def test_no_save_without_flag(self, tmp_path, create_test_images):
        """Test that JSON is not saved without --save-json flag."""
        test_dir = tmp_path / "photos"
        test_dir.mkdir()
        create_test_images(test_dir, count=1)
        
        cache_dir = tmp_path / "cache"
        cache_dir.mkdir()
        
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(find_samples, ['-s', str(test_dir)])
        
        assert result.exit_code == 0
        json_file = cache_dir / "photos.json"
        assert not json_file.exists()
    
    def test_overwrite_existing_json(self, tmp_path, create_test_images):
        """Test overwriting existing JSON file."""
        test_dir = tmp_path / "photos"
        test_dir.mkdir()
        create_test_images(test_dir, count=2)
        
        json_file = tmp_path / "photos.json"
        # Create existing file with different content
        json_file.write_text('{"old": "data"}')
        
        runner = CliRunner()
        result = runner.invoke(find_samples, [
            '-s', str(test_dir),
            '--save-json',
            '--cache-file', str(json_file)
        ])
        
        assert result.exit_code == 0
        
        with open(json_file) as f:
            data = json.load(f)
        
        # Should have new structure, not old
        assert "photos" in data
        assert "old" not in data


@pytest.fixture
def create_test_images_with_exif(create_fake_photo_with_exif):
    """Create test images with specific EXIF data."""
    def _create(directory, photo_specs):
        created_files = []
        for spec in photo_specs:
            photo_path = directory / spec["filename"]
            create_fake_photo_with_exif(
                photo_path,
                timestamp_str=spec.get("timestamp"),
                camera_make=spec.get("make"),
                camera_model=spec.get("model"),
                subsec=spec.get("subsec")
            )
            created_files.append(photo_path)
        return created_files
    return _create