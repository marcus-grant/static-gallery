"""Tests for file processing service."""

import pytest
from pathlib import Path
from PIL import Image
from src.services.file_processing import (
    link_photo_with_filename, 
    create_thumbnail,
    process_photo_collection,
    THUMBNAIL_SIZE
)
from src.models.photo import ProcessedPhoto, CameraInfo, ExifData
from datetime import datetime


@pytest.fixture
def temp_photo(tmp_path):
    """Create a temporary photo file."""
    photo_path = tmp_path / "IMG_001.jpg"
    img = Image.new('RGB', (100, 100), color='red')
    img.save(photo_path)
    return photo_path


class TestLinkPhoto:
    """Test link_photo_with_filename function."""
    
    def test_link_photo_basic(self, temp_photo, tmp_path):
        """Test basic photo symlinking."""
        output_dir = tmp_path / "output"
        photo = ProcessedPhoto(
            path=temp_photo,
            filename="IMG_001.jpg",
            file_size=1024,
            camera=CameraInfo(make="Canon", model="EOS R5"),
            exif=ExifData(
                timestamp=datetime(2024, 10, 5, 14, 30, 45),
                subsecond=123,
                gps_latitude=None,
                gps_longitude=None,
                raw_data={}
            ),
            edge_cases=[],
            generated_filename="wedding-20241005T143045.123Z0400-r5a-001.jpg"
        )
        
        new_path = link_photo_with_filename(photo, output_dir)
        
        assert new_path.exists()
        assert new_path.is_symlink()  # Should be a symlink
        assert new_path.resolve() == temp_photo.absolute()  # Should point to original
        assert new_path.name == "wedding-20241005T143045.123Z0400-r5a-001.jpg"
        assert temp_photo.exists()  # Original should still exist
        assert output_dir.exists()
    
    def test_link_photo_no_generated_filename(self, temp_photo, tmp_path):
        """Test error when no generated filename."""
        photo = ProcessedPhoto(
            path=temp_photo,
            filename="IMG_001.jpg", 
            file_size=1024,
            camera=CameraInfo(make="Canon", model="EOS R5"),
            exif=ExifData(
                timestamp=None,
                subsecond=None,
                gps_latitude=None,
                gps_longitude=None,
                raw_data={}
            ),
            edge_cases=[],
            generated_filename=None
        )
        
        with pytest.raises(ValueError, match="No generated filename"):
            link_photo_with_filename(photo, tmp_path / "output")


class TestCreateThumbnail:
    """Test create_thumbnail function."""
    
    def test_create_thumbnail_basic(self, temp_photo, tmp_path):
        """Test basic thumbnail creation."""
        thumb_path = tmp_path / "thumb.webp"
        
        success = create_thumbnail(temp_photo, thumb_path)
        
        assert success
        assert thumb_path.exists()
        
        # Check it's a WebP
        with Image.open(thumb_path) as img:
            assert img.format == "WEBP"
            assert max(img.size) <= THUMBNAIL_SIZE


class TestProcessPhotoCollection:
    """Test process_photo_collection function."""
    
    def test_process_empty_collection(self, tmp_path):
        """Test processing empty directory."""
        source_dir = tmp_path / "source"
        output_dir = tmp_path / "output"
        source_dir.mkdir()
        
        result = process_photo_collection(
            source_dir=source_dir,
            output_dir=output_dir,
            collection_name="test"
        )
        
        assert result["total_processed"] == 0
        assert result["errors"] == []
        assert result["photos"] == []
    
    def test_process_single_photo(self, tmp_path):
        """Test processing a single photo."""
        # Setup directories
        source_dir = tmp_path / "source"
        output_dir = tmp_path / "output"
        source_dir.mkdir()
        
        # Create test photo
        test_image = Image.new('RGB', (800, 600), color='blue')
        photo_path = source_dir / "IMG_001.jpg"
        test_image.save(photo_path)
        
        # Process collection
        result = process_photo_collection(
            source_dir=source_dir,
            output_dir=output_dir,
            collection_name="wedding"
        )
        
        # Check results
        assert result["total_processed"] == 1
        assert len(result["photos"]) == 1
        
        # Check output structure
        assert (output_dir / "full").exists()
        assert (output_dir / "thumb").exists()
        
        # Check that files were created
        full_files = list((output_dir / "full").iterdir())
        thumb_files = list((output_dir / "thumb").iterdir())
        
        assert len(full_files) == 1
        assert len(thumb_files) == 1
        assert full_files[0].is_symlink()
        assert thumb_files[0].suffix == ".webp"