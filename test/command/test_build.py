"""Tests for build command."""

import pytest
from click.testing import CliRunner
from pathlib import Path
from unittest.mock import patch, Mock


def test_build_command_exists_and_outputs_status():
    """Test that build command exists and outputs status messages."""
    from manage import cli

    runner = CliRunner()
    result = runner.invoke(cli, ["build"])

    # Command should run without crashing
    assert result.exit_code == 0

    # Output should contain status keywords
    output_keywords = ["build", "site", "generating"]
    for keyword in output_keywords:
        assert keyword.lower() in result.output.lower()


def test_build_reports_directory_status():
    """Test that build command reports on directory status."""
    from manage import cli

    runner = CliRunner()
    with runner.isolated_filesystem():
        result = runner.invoke(cli, ["build"])

        # Should report about source and output directories
        assert "prod/pics" in result.output
        assert "prod/site" in result.output

        # Should mention directory creation or existence
        directory_keywords = ["creating", "exists", "directories", "structure"]
        assert any(keyword in result.output.lower() for keyword in directory_keywords)


def test_build_reports_missing_source_directory():
    """Test that build command reports when source directory doesn't exist."""
    from manage import cli

    runner = CliRunner()
    with runner.isolated_filesystem():
        # prod/pics doesn't exist in isolated filesystem
        result = runner.invoke(cli, ["build"])

        # Should report that source directory doesn't exist
        assert "prod/pics" in result.output
        assert any(
            word in result.output.lower()
            for word in ["not found", "does not exist", "missing"]
        )


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
        result = runner.invoke(cli, ["build"])

        # Check output directory was created
        output_dir = Path.cwd() / "prod" / "site"
        assert output_dir.exists()
        assert output_dir.is_dir()

        # Check subdirectories were created
        assert (output_dir / "css").exists()
        assert (output_dir / "js").exists()

        # Check output mentions creation
        assert "creating" in result.output.lower() or "created" in result.output.lower()


def test_build_command_calls_build_gallery_function():
    """Test that build command calls the build_gallery function properly."""
    from manage import cli
    from unittest.mock import patch
    
    runner = CliRunner()
    
    # Mock the build_gallery function and directory checks
    mock_build_result = {
        'success': True,
        'photos_processed': 5,
        'gallery_generated': True
    }
    
    with patch('src.command.build.build_gallery', return_value=mock_build_result) as mock_build_gallery:
        with patch('src.command.build.check_source_directory', return_value=True):
            with patch('src.command.build.check_source_subdirectories', return_value={}):
                result = runner.invoke(cli, ["build"])
                
                # Verify the command called build_gallery
                assert result.exit_code == 0
                mock_build_gallery.assert_called_once()
                
                # Verify output reflects the results
                assert "5 photos" in result.output
                assert "Gallery page created" in result.output
                assert "Build complete" in result.output


def test_build_gallery_function_orchestrates_services():
    """Test that build_gallery function calls correct services with proper orchestration."""
    from src.command.build import build_gallery
    
    # Mock photo data that PhotoMetadataService would return
    mock_photo_data = {
        'photos': [{'filename': 'wedding-20250809T132034.jpg', 'timestamp': '2024-01-01'}],
        'total_count': 1
    }
    
    with patch('src.command.build.PhotoMetadataService') as mock_metadata_service:
        with patch('src.command.build.TemplateRenderer') as mock_renderer_class:
            with patch('src.command.build.create_output_directory_structure') as mock_create_dir:
                with patch('pathlib.Path.exists', return_value=True):
                    # Setup mocks
                    mock_metadata_instance = Mock()
                    mock_metadata_service.return_value = mock_metadata_instance
                    mock_metadata_instance.generate_json_metadata.return_value = mock_photo_data
                    
                    mock_renderer_instance = Mock()
                    mock_renderer_class.return_value = mock_renderer_instance
                    mock_renderer_instance.render.return_value = "<html>Gallery HTML</html>"
                    
                    mock_create_dir.return_value = {'created': True}
                    
                    # Call the pure function
                    result = build_gallery()
                    
                    # Verify return value
                    assert result['success'] == True
                    assert result['photos_processed'] == 1
                    assert result['gallery_generated'] == True
                    
                    # Verify service orchestration
                    mock_metadata_service.assert_called_once()
                    mock_metadata_instance.generate_json_metadata.assert_called_once()
                    
                    mock_renderer_class.assert_called_once()
                    # Verify both templates were rendered
                    assert mock_renderer_instance.render.call_count == 2
                    mock_renderer_instance.render.assert_any_call("gallery.j2.html", mock_photo_data)
                    mock_renderer_instance.render.assert_any_call("index.j2.html", mock_photo_data)
                    
                    # Verify both HTML files were saved
                    assert mock_renderer_instance.save_html.call_count == 2
                    mock_renderer_instance.save_html.assert_any_call("<html>Gallery HTML</html>", "prod/site/gallery.html")
                    mock_renderer_instance.save_html.assert_any_call("<html>Gallery HTML</html>", "prod/site/index.html")
                    
                    mock_create_dir.assert_called_once()


def test_build_gallery_function_handles_no_photos():
    """Test that build_gallery function handles case when no photos are found."""
    from src.command.build import build_gallery
    
    # Mock empty photo data
    mock_photo_data = {
        'photos': [],
        'total_count': 0
    }
    
    with patch('src.command.build.PhotoMetadataService') as mock_metadata_service:
        with patch('src.command.build.create_output_directory_structure') as mock_create_dir:
            # Setup mocks
            mock_metadata_instance = Mock()
            mock_metadata_service.return_value = mock_metadata_instance
            mock_metadata_instance.generate_json_metadata.return_value = mock_photo_data
            mock_create_dir.return_value = {'created': True}
            
            # Call the pure function
            result = build_gallery()
            
            # Verify return value
            assert result['success'] == True
            assert result['photos_processed'] == 0
            assert result['gallery_generated'] == False
            
            # Verify only metadata service was called, not renderer
            mock_metadata_service.assert_called_once()
            mock_create_dir.assert_called_once()

