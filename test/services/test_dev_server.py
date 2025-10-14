import tempfile
import os
import time
from pathlib import Path
from unittest.mock import patch, Mock, MagicMock, call
import pytest
import threading
from src.services.dev_server import DevServer


def test_dev_server_initializes_with_defaults():
    """Test that DevServer initializes with default values"""
    server = DevServer()
    
    assert server.port == 8000
    assert server.directory == "prod/site"
    assert server.reload is False


def test_dev_server_initializes_with_custom_values():
    """Test that DevServer accepts custom initialization values"""
    server = DevServer(port=9000, directory="custom/dir", reload=True)
    
    assert server.port == 9000
    assert server.directory == "custom/dir"
    assert server.reload is True


def test_dev_server_serves_existing_files():
    """Test that DevServer serves existing files correctly"""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test file
        test_file = Path(temp_dir) / "test.html"
        test_file.write_text("<html>Test Content</html>")
        
        server = DevServer(directory=temp_dir)
        
        # Mock HTTP request for the file
        mock_request = Mock()
        mock_request.path = "/test.html"
        
        with patch('src.services.dev_server.SimpleHTTPRequestHandler') as mock_handler:
            handler_instance = Mock()
            mock_handler.return_value = handler_instance
            
            # Test that file gets served
            response = server.handle_request(mock_request)
            
            # Should not return 404
            assert response != 404


def test_dev_server_returns_404_for_missing_files():
    """Test that DevServer returns 404 for missing files"""
    with tempfile.TemporaryDirectory() as temp_dir:
        server = DevServer(directory=temp_dir)
        
        # Mock HTTP request for non-existent file
        mock_request = Mock()
        mock_request.path = "/nonexistent.html"
        
        response = server.handle_request(mock_request)
        
        assert response == 404


def test_dev_server_serves_gallery_route():
    """Test that /gallery route serves gallery.html"""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create gallery.html
        gallery_file = Path(temp_dir) / "gallery.html"
        gallery_file.write_text("<html>Gallery Page</html>")
        
        server = DevServer(directory=temp_dir)
        
        # Mock request to /gallery
        mock_request = Mock()
        mock_request.path = "/gallery"
        
        with patch('src.services.dev_server.SimpleHTTPRequestHandler') as mock_handler:
            handler_instance = Mock()
            mock_handler.return_value = handler_instance
            
            response = server.handle_request(mock_request)
            
            # Should serve gallery.html, not 404
            assert response != 404


def test_dev_server_returns_404_for_root_without_index():
    """Test that / returns 404 when no index.html exists"""
    with tempfile.TemporaryDirectory() as temp_dir:
        server = DevServer(directory=temp_dir)
        
        # Mock request to root
        mock_request = Mock()
        mock_request.path = "/"
        
        response = server.handle_request(mock_request)
        
        assert response == 404


def test_dev_server_sets_up_file_watcher_when_reload_enabled():
    """Test that file watcher is set up when reload is enabled"""
    server = DevServer(reload=True)
    
    with patch.object(server, 'start_server'):
        with patch.object(server, 'setup_file_watcher') as mock_setup:
            server.start()
    
    # Verify file watcher setup was called
    mock_setup.assert_called_once()


def test_dev_server_triggers_rebuild_on_file_change():
    """Test that file changes trigger a rebuild"""
    server = DevServer(reload=True)
    
    with patch.object(server, 'rebuild_site') as mock_rebuild:
        # Simulate file change event
        server.on_file_changed("src/template/gallery.j2.html")
        
        mock_rebuild.assert_called_once()


def test_dev_server_rebuild_calls_build_command():
    """Test that rebuild calls the build command"""
    server = DevServer()
    
    with patch('subprocess.run') as mock_run:
        mock_run.return_value.returncode = 0
        
        server.rebuild_site()
        
        # Should call python manage.py build
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert "manage.py" in call_args
        assert "build" in call_args