"""Tests for photo validation services."""
import pytest
from pathlib import Path
from PIL import Image

from src.services.photo_validation import (
    get_photo_filename_mapping,
    validate_matching_collections,
    get_matched_photo_pairs
)


class TestPhotoFilenameMapping:
    """Test get_photo_filename_mapping function."""
    
    def test_empty_directory(self, tmp_path):
        """Test mapping of empty directory."""
        result = get_photo_filename_mapping(tmp_path)
        assert result == {}
    
    def test_single_photo(self, tmp_path):
        """Test mapping with single photo."""
        img = Image.new('RGB', (100, 100))
        img.save(tmp_path / "IMG_001.jpg")
        
        result = get_photo_filename_mapping(tmp_path)
        assert len(result) == 1
        assert "IMG_001" in result
        assert result["IMG_001"].name == "IMG_001.jpg"
    
    def test_multiple_photos_same_stem(self, tmp_path):
        """Test that only image files are included."""
        # Create photos with same stem but different extensions
        img = Image.new('RGB', (100, 100))
        img.save(tmp_path / "photo.jpg")
        img.save(tmp_path / "photo.png")
        
        # Create non-image file
        (tmp_path / "photo.txt").write_text("not an image")
        
        result = get_photo_filename_mapping(tmp_path)
        # Should only have one entry per stem
        assert len(result) == 1
        assert "photo" in result


class TestValidateMatchingCollections:
    """Test validate_matching_collections function."""
    
    def test_identical_collections(self, tmp_path):
        """Test validation with identical collections."""
        full_dir = tmp_path / "full"
        web_dir = tmp_path / "web"
        full_dir.mkdir()
        web_dir.mkdir()
        
        # Create same photos in both
        for name in ["IMG_001.jpg", "IMG_002.jpg"]:
            Image.new('RGB', (100, 100)).save(full_dir / name)
            Image.new('RGB', (50, 50)).save(web_dir / name)
        
        matched, full_only, web_only = validate_matching_collections(full_dir, web_dir)
        
        assert len(matched) == 2
        assert "IMG_001" in matched
        assert "IMG_002" in matched
        assert full_only == []
        assert web_only == []
    
    def test_mismatched_collections(self, tmp_path):
        """Test validation with mismatched collections."""
        full_dir = tmp_path / "full"
        web_dir = tmp_path / "web"
        full_dir.mkdir()
        web_dir.mkdir()
        
        # Create overlapping but different sets
        Image.new('RGB', (100, 100)).save(full_dir / "IMG_001.jpg")
        Image.new('RGB', (100, 100)).save(full_dir / "IMG_002.jpg")
        Image.new('RGB', (100, 100)).save(full_dir / "IMG_003.jpg")
        
        Image.new('RGB', (50, 50)).save(web_dir / "IMG_002.jpg")
        Image.new('RGB', (50, 50)).save(web_dir / "IMG_003.jpg")
        Image.new('RGB', (50, 50)).save(web_dir / "IMG_004.jpg")
        
        matched, full_only, web_only = validate_matching_collections(full_dir, web_dir)
        
        assert matched == ["IMG_002", "IMG_003"]
        assert full_only == ["IMG_001"]
        assert web_only == ["IMG_004"]