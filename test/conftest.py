"""Shared test fixtures."""

import pytest
from pathlib import Path
from PIL import Image

try:
    import piexif
    HAS_PIEXIF = True
except ImportError:
    HAS_PIEXIF = False


@pytest.fixture
def create_test_images():
    """Create basic test images without EXIF."""
    def _create(directory, count=1):
        created_files = []
        for i in range(count):
            img = Image.new("RGB", (100, 100), color="red")
            photo_path = directory / f"IMG_{i+1:03d}.jpg"
            img.save(photo_path, "JPEG")
            created_files.append(photo_path)
        return created_files
    return _create


@pytest.fixture
def create_fake_photo_with_exif():
    """Create a fake photo with specific EXIF data."""
    def _create(photo_path, timestamp_str=None, camera_make=None, 
                camera_model=None, subsec=None):
        img = Image.new("RGB", (100, 100), color="red")
        
        if HAS_PIEXIF and (timestamp_str or camera_make or camera_model or subsec is not None):
            exif_dict = {"0th": {}, "Exif": {}, "1st": {}, "GPS": {}}
            
            if timestamp_str:
                exif_dict["Exif"][piexif.ExifIFD.DateTimeOriginal] = timestamp_str.encode()
            
            if camera_make:
                exif_dict["0th"][piexif.ImageIFD.Make] = camera_make.encode()
                
            if camera_model:
                exif_dict["0th"][piexif.ImageIFD.Model] = camera_model.encode()
                
            if subsec is not None:
                exif_dict["Exif"][piexif.ExifIFD.SubSecTimeOriginal] = str(subsec).encode()
            
            exif_bytes = piexif.dump(exif_dict)
            img.save(photo_path, "JPEG", exif=exif_bytes)
        else:
            # Save without EXIF if piexif not available or no EXIF data requested
            img.save(photo_path, "JPEG")
            
        return photo_path
    
    return _create