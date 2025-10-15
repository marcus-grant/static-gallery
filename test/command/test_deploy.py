"""Tests for deploy command."""
import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch
from click.testing import CliRunner

from src.command.deploy import deploy


class TestDeployCommandInterface:
    """Test deploy command CLI interface and input validation."""
    
    def test_help_message(self):
        """Test deploy command shows help message with all options."""
        runner = CliRunner()
        result = runner.invoke(deploy, ['--help'])
        
        assert result.exit_code == 0
        assert "Deploy complete gallery" in result.output
        assert "--source" in result.output
        assert "--dry-run" in result.output
        assert "--invalidate-cdn" in result.output
        assert "--photos-only" in result.output
        assert "--site-only" in result.output
    
    def test_source_directory_validation_nonexistent(self):
        """Test command validates source directory exists."""
        runner = CliRunner()
        
        result = runner.invoke(deploy, ['--source', '/nonexistent/path'])
        
        assert result.exit_code == 2
        assert "does not exist" in result.output
    
    def test_mutually_exclusive_options(self):
        """Test --photos-only and --site-only are mutually exclusive."""
        runner = CliRunner()
        
        result = runner.invoke(deploy, ['--photos-only', '--site-only'])
        
        assert result.exit_code == 1
        assert "mutually exclusive" in result.output or "cannot be used together" in result.output


class TestDeployCommandFunctionality:
    """Test deploy command deployment functionality."""
    
    def test_successful_deployment(self, tmp_path):
        """Test successful deployment of both photos and static site."""
        runner = CliRunner()
        
        # Create test source directory
        source_dir = tmp_path / "output"
        source_dir.mkdir()
        (source_dir / "index.html").write_text("<html></html>")
        
        mock_settings = Mock()
        mock_settings.OUTPUT_DIR = source_dir
        mock_settings.BASE_DIR = tmp_path
        # Create prod/pics directory structure
        prod_pics = tmp_path / "prod" / "pics"
        prod_pics.mkdir(parents=True)
        
        with patch.dict(sys.modules, {'settings': mock_settings}):
            with patch('src.command.deploy.validate_s3_config', return_value=(True, "")):
                with patch('src.command.deploy.get_s3_client') as mock_client:
                    with patch('src.command.deploy.deploy_directory_to_s3') as mock_deploy:
                        mock_deploy.return_value = {
                            'success': True,
                            'total_files': 2,
                            'uploaded_files': 2,
                            'skipped_files': 0,
                            'failed_files': 0,
                            'total_size': 1024,
                            'errors': []
                        }
                        
                        result = runner.invoke(deploy)
                        
                        assert result.exit_code == 0
                        assert "Deployment completed successfully" in result.output
                        assert mock_deploy.call_count == 2  # photos + static site
    
    def test_photos_only_deployment(self, tmp_path):
        """Test deployment with --photos-only flag."""
        runner = CliRunner()
        
        mock_settings = Mock()
        mock_settings.BASE_DIR = tmp_path
        # Create prod/pics directory structure
        prod_pics = tmp_path / "prod" / "pics"
        prod_pics.mkdir(parents=True)
        
        with patch.dict(sys.modules, {'settings': mock_settings}):
            with patch('src.command.deploy.validate_s3_config', return_value=(True, "")):
                with patch('src.command.deploy.get_s3_client'):
                    with patch('src.command.deploy.deploy_directory_to_s3') as mock_deploy:
                        mock_deploy.return_value = {
                            'success': True, 
                            'total_files': 1,
                            'uploaded_files': 1,
                            'skipped_files': 0,
                            'failed_files': 0,
                            'errors': []
                        }
                        
                        result = runner.invoke(deploy, ['--photos-only'])
                        
                        assert result.exit_code == 0
                        assert mock_deploy.call_count == 1  # Only photos
                        args, kwargs = mock_deploy.call_args
                        assert kwargs['prefix'] == 'photos'
    
    def test_site_only_deployment(self, tmp_path):
        """Test deployment with --site-only flag."""
        runner = CliRunner()
        
        source_dir = tmp_path / "output"
        source_dir.mkdir()
        
        mock_settings = Mock()
        mock_settings.OUTPUT_DIR = source_dir
        mock_settings.BASE_DIR = tmp_path
        
        with patch.dict(sys.modules, {'settings': mock_settings}):
            with patch('src.command.deploy.validate_s3_config', return_value=(True, "")):
                with patch('src.command.deploy.get_s3_client'):
                    with patch('src.command.deploy.deploy_directory_to_s3') as mock_deploy:
                        mock_deploy.return_value = {
                            'success': True, 
                            'total_files': 1,
                            'uploaded_files': 1,
                            'skipped_files': 0,
                            'failed_files': 0,
                            'errors': []
                        }
                        
                        result = runner.invoke(deploy, ['--site-only'])
                        
                        assert result.exit_code == 0
                        assert mock_deploy.call_count == 1  # Only static site
                        args, kwargs = mock_deploy.call_args
                        assert kwargs['prefix'] == ''