import click
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
from click.testing import CliRunner
from pyfakefs.fake_filesystem_unittest import Patcher

from src.command import find_samples


class TestFindSamplesCommand:
    def test_command_exists(self):
        assert hasattr(find_samples, "find_samples")

    def test_find_samples_is_click_command(self):
        assert isinstance(find_samples.find_samples, click.core.Command)

    def test_find_samples_has_pic_source_path_full_option(self):
        # Test that the command has a pic_source_path_full option
        params = [p.name for p in find_samples.find_samples.params]
        assert "pic_source_path_full" in params

    def test_cli_arg_overrides_env_var(self):
        # Test that CLI arg overrides env var for pic_source_path_full
        runner = CliRunner()

        with Patcher() as patcher:
            fs = patcher.fs
            fs.create_dir("/cli_path")
            fs.create_dir("/env_path")
            fs.create_dir("/cache")

            with patch.dict(os.environ, {"GALLERIA_PIC_SOURCE_PATH_FULL": "/env_path"}):
                result = runner.invoke(
                    find_samples.find_samples,
                    ["--pic-source-path-full", "/cli_path"],
                )

                if result.exit_code != 0:
                    print(f"Error: {result.exception}")
                assert result.exit_code == 0
                # CLI arg path should be used, not env var path
                assert "/cli_path" in result.output
                assert "/env_path" not in result.output

    def test_find_samples_scans_directory_for_photos(self):
        # Test that find-samples command scans directory and finds photos
        runner = CliRunner()

        with Patcher() as patcher:
            fs = patcher.fs
            # Create test directory with photos in fake filesystem
            fs.create_dir("/test_pics")
            fs.create_file("/test_pics/photo1.jpg")
            fs.create_file("/test_pics/photo2.jpeg")
            fs.create_file("/test_pics/not_photo.txt")
            fs.create_dir("/cache")

            result = runner.invoke(
                find_samples.find_samples, ["--pic-source", "/test_pics"]
            )

            assert result.exit_code == 0
            assert "Found 2 photos" in result.output
            assert "photo1.jpg" in result.output
            assert "photo2.jpeg" in result.output
            assert "not_photo.txt" not in result.output

    def test_find_samples_uses_fs_module(self):
        # Test that find_samples uses fs.ls_full instead of manual scanning
        runner = CliRunner()

        mock_path = "src.command.find_samples.fs.ls_full"
        settings_path = "src.command.find_samples.settings.PIC_SOURCE_PATH_FULL"

        with patch(mock_path, return_value=[]) as mock_ls_full:
            with patch(settings_path, Path("/pics")):
                with Patcher() as patcher:
                    patcher.fs.create_dir("/pics")
                    result = runner.invoke(find_samples.find_samples)

        assert result.exit_code == 0
        mock_ls_full.assert_called_once_with(None)
        assert "Found 0 photos" in result.output
    
    def test_find_samples_with_bursts_filter(self):
        """Test that find_samples can filter for burst sequences"""
        runner = CliRunner()
        
        with Patcher() as patcher:
            fs = patcher.fs
            fs.create_dir("/test_pics")
            # Create fake photos that would be in a burst
            fs.create_file("/test_pics/burst1.jpg")
            fs.create_file("/test_pics/burst2.jpg") 
            fs.create_file("/test_pics/single.jpg")
            fs.create_dir("/cache")
            
            # Mock the EXIF service to return burst sequences
            mock_exif_path = "src.command.find_samples.exif"
            with patch(mock_exif_path) as mock_exif:
                # Mock sort_photos_chronologically
                mock_exif.sort_photos_chronologically.return_value = [
                    (Path("/test_pics/burst1.jpg"), MagicMock(), {}),
                    (Path("/test_pics/burst2.jpg"), MagicMock(), {}),
                    (Path("/test_pics/single.jpg"), MagicMock(), {})
                ]
                # Mock detect_burst_sequences to return one burst
                mock_exif.detect_burst_sequences.return_value = [
                    [Path("/test_pics/burst1.jpg"), Path("/test_pics/burst2.jpg")]
                ]
                
                result = runner.invoke(
                    find_samples.find_samples, 
                    ["--pic-source", "/test_pics", "--show-bursts"]
                )
                
                assert result.exit_code == 0
                assert "Burst sequence (2 photos):" in result.output
                assert "burst1.jpg" in result.output
                assert "burst2.jpg" in result.output
    
    def test_find_samples_with_missing_exif_filter(self):
        """Test that find_samples can filter for photos without EXIF"""
        runner = CliRunner()
        
        with Patcher() as patcher:
            fs = patcher.fs
            fs.create_dir("/test_pics")
            # Create fake photos
            fs.create_file("/test_pics/good.jpg")
            fs.create_file("/test_pics/no_exif.jpg")
            fs.create_dir("/cache")
            
            # Mock the EXIF service
            mock_exif_path = "src.command.find_samples.exif"
            with patch(mock_exif_path) as mock_exif:
                # Mock find_missing_exif_photos to return one photo
                mock_exif.find_missing_exif_photos.return_value = [
                    Path("/test_pics/no_exif.jpg")
                ]
                
                result = runner.invoke(
                    find_samples.find_samples, 
                    ["--pic-source", "/test_pics", "--show-missing-exif"]
                )
                
                assert result.exit_code == 0
                assert "Found 1 photo(s) without EXIF timestamps:" in result.output
                assert "no_exif.jpg" in result.output
                assert "good.jpg" not in result.output
