import tempfile
import os
from pathlib import Path
from unittest.mock import patch, Mock, MagicMock
import pytest
from click.testing import CliRunner
from src.command.serve import serve


def test_serve_command_exists():
    """Test that serve command exists and is callable"""
    runner = CliRunner()
    result = runner.invoke(serve, ['--help'])
    
    # Command should exist and show help
    assert result.exit_code == 0
    assert 'serve' in result.output.lower()


def test_serve_command_starts_http_server():
    """Test that serve command starts an HTTP server"""
    runner = CliRunner()
    
    with patch('src.command.serve.DevServer') as mock_dev_server:
        mock_server_instance = Mock()
        mock_dev_server.return_value = mock_server_instance
        
        # Run serve command (should exit quickly in test)
        result = runner.invoke(serve, ['--port', '8888'])
        
        # Verify DevServer was created and started
        mock_dev_server.assert_called_once()
        mock_server_instance.start.assert_called_once()


def test_serve_command_accepts_port_option():
    """Test that serve command accepts --port option"""
    runner = CliRunner()
    
    with patch('src.command.serve.DevServer') as mock_dev_server:
        mock_server_instance = Mock()
        mock_dev_server.return_value = mock_server_instance
        
        runner.invoke(serve, ['--port', '9000'])
        
        # Check that DevServer was initialized with correct port
        call_args = mock_dev_server.call_args
        assert 'port' in call_args.kwargs
        assert call_args.kwargs['port'] == 9000


def test_serve_command_accepts_reload_option():
    """Test that serve command accepts --reload option"""
    runner = CliRunner()
    
    with patch('src.command.serve.DevServer') as mock_dev_server:
        mock_server_instance = Mock()
        mock_dev_server.return_value = mock_server_instance
        
        runner.invoke(serve, ['--reload'])
        
        # Check that DevServer was initialized with reload enabled
        call_args = mock_dev_server.call_args
        assert 'reload' in call_args.kwargs
        assert call_args.kwargs['reload'] is True


def test_serve_command_serves_from_prod_site():
    """Test that serve command serves from prod/site directory"""
    runner = CliRunner()
    
    with patch('src.command.serve.DevServer') as mock_dev_server:
        mock_server_instance = Mock()
        mock_dev_server.return_value = mock_server_instance
        
        runner.invoke(serve)
        
        # Check that DevServer was initialized with correct directory
        call_args = mock_dev_server.call_args
        assert 'directory' in call_args.kwargs
        assert 'prod/site' in call_args.kwargs['directory']