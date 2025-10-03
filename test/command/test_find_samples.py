import pytest
import click
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
from click.testing import CliRunner
from pyfakefs.fake_filesystem_unittest import Patcher
from PIL import Image
import piexif
from src.command import find_samples
from src.command.find_samples import find_samples as find_samples_cmd


@pytest.fixture
def create_photo_with_camera_info(tmp_path):
    """Creates test photos with specific camera info"""
    def _create(filename, **exif_tags):
        img = Image.new("RGB", (100, 100), color="red")
        photo_path = tmp_path / filename
        
        if exif_tags:
            exif_dict = {"0th": {}, "Exif": {}, "1st": {}, "GPS": {}}
            
            if "DateTimeOriginal" in exif_tags:
                exif_dict["Exif"][piexif.ExifIFD.DateTimeOriginal] = exif_tags["DateTimeOriginal"].encode()
            if "Make" in exif_tags:
                exif_dict["0th"][piexif.ImageIFD.Make] = exif_tags["Make"].encode()
            if "Model" in exif_tags:
                exif_dict["0th"][piexif.ImageIFD.Model] = exif_tags["Model"].encode()
            
            exif_bytes = piexif.dump(exif_dict)
            img.save(photo_path, "JPEG", exif=exif_bytes)
        else:
            img.save(photo_path, "JPEG")
            
        return photo_path
    
    return _create


class TestFindSamplesCameraFormatting:
    """Test camera name formatting in find-samples command"""
    
    def test_unknown_camera_formatting(self, create_photo_with_camera_info, tmp_path):
        """Test that photos without camera info show as 'Unknown camera'"""
        # Create photos with no EXIF
        create_photo_with_camera_info("no_exif_1.jpg")
        create_photo_with_camera_info("no_exif_2.jpg")
        create_photo_with_camera_info("no_exif_3.jpg")
        
        runner = CliRunner()
        result = runner.invoke(find_samples_cmd, ['-s', str(tmp_path), '--show-camera-diversity'])
        
        assert result.exit_code == 0
        # Should display "Unknown camera" not "Unknown Unknown"  
        assert "Unknown camera: 3 photos" in result.output
        assert "Unknown Unknown" not in result.output


class TestFindSamplesCameraSorting:
    """Test camera sorting with None values"""
    
    def test_camera_groups_sort_with_none_values(self, create_photo_with_camera_info, tmp_path):
        """Test that camera groups can be sorted even with None values"""
        # Create diverse camera scenarios
        create_photo_with_camera_info("canon.jpg", Make="Canon", Model="EOS 5D")
        create_photo_with_camera_info("no_info.jpg")  # Will have (None, None)
        create_photo_with_camera_info("partial.jpg", Model="Mystery")  # (None, "Mystery")
        create_photo_with_camera_info("apple.jpg", Make="Apple", Model="iPhone")
        
        runner = CliRunner()
        result = runner.invoke(find_samples_cmd, ['-s', str(tmp_path), '--show-camera-diversity'])
        
        # Should not crash with TypeError about comparing None
        assert result.exit_code == 0
        assert "TypeError" not in result.output
        assert "Found 4 different camera(s):" in result.output