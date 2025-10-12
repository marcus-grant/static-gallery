"""Tests for process-photos command."""
import pytest
from pathlib import Path
from click.testing import CliRunner
from PIL import Image

from src.command.process_photos import process_photos


class TestProcessPhotosCommand:
    """Test process-photos command."""
    
    def test_command_exists(self):
        """Test that command is properly defined."""
        assert process_photos is not None
        assert hasattr(process_photos, 'callback')
    
    def test_missing_directories(self):
        """Test command fails when directories don't exist."""
        runner = CliRunner()
        
        result = runner.invoke(process_photos, [
            '--full-source', '/nonexistent/full',
            '--web-source', '/nonexistent/web'
        ])
        
        # Click returns exit code 2 for path validation errors
        assert result.exit_code == 2
        assert "does not exist" in result.output
    
    def test_dry_run_with_matching_photos(self, tmp_path):
        """Test dry run with matching photo collections."""
        # Create test directories
        full_dir = tmp_path / "full"
        web_dir = tmp_path / "web"
        output_dir = tmp_path / "output"
        
        full_dir.mkdir()
        web_dir.mkdir()
        
        # Create matching photos
        for name in ["IMG_001.jpg", "IMG_002.jpg"]:
            Image.new('RGB', (100, 100)).save(full_dir / name)
            Image.new('RGB', (50, 50)).save(web_dir / name)
        
        runner = CliRunner()
        result = runner.invoke(process_photos, [
            '--full-source', str(full_dir),
            '--web-source', str(web_dir),
            '--output', str(output_dir),
            '--dry-run'
        ])
        
        assert result.exit_code == 0
        assert "Matched photos: 2" in result.output
        assert "Would process 2 matching photos" in result.output