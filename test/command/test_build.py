"""Tests for build command."""
import pytest
from click.testing import CliRunner
from pathlib import Path


def test_build_command_exists_and_outputs_status():
    """Test that build command exists and outputs status messages."""
    from manage import cli
    
    runner = CliRunner()
    result = runner.invoke(cli, ['build'])
    
    # Command should run without crashing
    assert result.exit_code == 0
    
    # Output should contain status keywords
    output_keywords = ['build', 'site', 'generating']
    for keyword in output_keywords:
        assert keyword.lower() in result.output.lower()


def test_build_reports_directory_status():
    """Test that build command reports on directory status."""
    from manage import cli
    
    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(cli, ['build'])
        
        # Should report about source and output directories
        assert 'prod/pics' in result.output
        assert 'prod/site' in result.output
        
        # Should mention directory creation or existence
        directory_keywords = ['creating', 'exists', 'directories', 'structure']
        assert any(keyword in result.output.lower() for keyword in directory_keywords)


def test_build_reports_missing_source_directory():
    """Test that build command reports when source directory doesn't exist."""
    from manage import cli
    
    runner = CliRunner()
    with runner.isolated_filesystem():
        # prod/pics doesn't exist in isolated filesystem
        result = runner.invoke(cli, ['build'])
        
        # Should report that source directory doesn't exist
        assert 'prod/pics' in result.output
        assert any(word in result.output.lower() for word in ['not found', 'does not exist', 'missing'])


def test_build_creates_output_directory_structure():
    """Test that build command creates output directory structure."""
    from manage import cli
    
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Create source structure
        source_dir = Path.cwd() / "prod" / "pics"
        source_dir.mkdir(parents=True)
        (source_dir / "full").mkdir()
        (source_dir / "web").mkdir()
        (source_dir / "thumb").mkdir()
        
        # Run build command
        result = runner.invoke(cli, ['build'])
        
        # Check output directory was created
        output_dir = Path.cwd() / "prod" / "site"
        assert output_dir.exists()
        assert output_dir.is_dir()
        
        # Check subdirectories were created
        assert (output_dir / "css").exists()
        assert (output_dir / "js").exists()
        
        # Check output mentions creation
        assert 'creating' in result.output.lower() or 'created' in result.output.lower()


def test_build_generates_gallery_html():
    """Test that build command generates gallery.html from processed photos."""
    from manage import cli
    
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Create source structure with a photo
        source_dir = Path.cwd() / "prod" / "pics"
        source_dir.mkdir(parents=True)
        (source_dir / "full").mkdir()
        (source_dir / "web").mkdir() 
        (source_dir / "thumb").mkdir()
        
        # Create a test photo
        test_photo = source_dir / "full" / "wedding-20250809T132034.000Z+0200-r5a-001.jpg"
        test_photo.write_text("fake photo content")
        
        # Create templates directory
        templates_dir = Path.cwd() / "templates"
        templates_dir.mkdir()
        gallery_template = templates_dir / "gallery.j2.html"
        gallery_template.write_text("<html>{{ photos|length }} photos</html>")
        
        # Run build command
        result = runner.invoke(cli, ['build'])
        
        # Check gallery.html was created
        gallery_html = Path.cwd() / "prod" / "site" / "gallery.html"
        assert gallery_html.exists()
        
        # Check content has photo data
        content = gallery_html.read_text()
        assert "1 photos" in content
        
        # Check output mentions HTML generation
        assert 'gallery' in result.output.lower()