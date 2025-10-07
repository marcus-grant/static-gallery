from pathlib import Path
from unittest.mock import patch
from pyfakefs.fake_filesystem_unittest import Patcher
from src.services.fs import ls_full


class TestLsFull:
    def test_returns_list(self):
        result = ls_full()
        assert isinstance(result, list)
    
    def test_finds_image_files(self):
        with Patcher() as patcher:
            fs = patcher.fs
            fs.create_dir("/pics")
            fs.create_file("/pics/photo1.jpg")
            fs.create_file("/pics/photo2.jpeg")
            fs.create_file("/pics/photo3.png")
            fs.create_file("/pics/document.txt")  # Should be ignored
            
            with patch('src.services.fs.settings.PIC_SOURCE_PATH_FULL', "/pics"):
                result = ls_full()
            
            assert len(result) == 3
            assert Path("/pics/photo1.jpg") in result
            assert Path("/pics/photo2.jpeg") in result
            assert Path("/pics/photo3.png") in result
    
    def test_path_parameter_overrides_settings(self):
        with Patcher() as patcher:
            fs = patcher.fs
            # Mock settings to point to empty directory
            fs.create_dir("/settings_path")  # Empty directory
            
            # Create custom path with test files
            fs.create_dir("/custom_path")
            fs.create_file("/custom_path/override_photo.jpg")
            
            with patch('src.services.fs.settings.PIC_SOURCE_PATH_FULL', "/settings_path"):
                result = ls_full("/custom_path")
            
            # Should find files in custom path, not settings path
            assert len(result) == 1
            assert Path("/custom_path/override_photo.jpg") in result