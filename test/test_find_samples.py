import pytest
import click
import os
from pathlib import Path
from unittest.mock import patch
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

            with patch.dict(os.environ, {"GALLERIA_PIC_SOURCE_PATH_FULL": "/env_path"}):
                result = runner.invoke(
                    find_samples.find_samples, ["--pic-source-path-full", "/cli_path"]
                )

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

            result = runner.invoke(
                find_samples.find_samples, ["--pic-source", "/test_pics"]
            )

            assert result.exit_code == 0
            assert "Found 2 photos" in result.output
            assert "photo1.jpg" in result.output
            assert "photo2.jpeg" in result.output
            assert "not_photo.txt" not in result.output
