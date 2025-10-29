"""Tests for deploy command."""
import pytest
import sys
import json
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
                    with patch('src.command.deploy.examine_bucket_cors') as mock_cors:
                        mock_cors.return_value = {
                            'success': True,
                            'configured': True,
                            'needs_update': False
                        }
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
                    with patch('src.command.deploy.examine_bucket_cors') as mock_cors:
                        mock_cors.return_value = {
                            'success': True,
                            'configured': True,
                            'needs_update': False
                        }
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
                    with patch('src.command.deploy.examine_bucket_cors') as mock_cors:
                        mock_cors.return_value = {
                            'success': True,
                            'configured': True,
                            'needs_update': False
                        }
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


class TestDeployCommandEnhanced:
    """Test enhanced deploy command with metadata-driven deployment."""
    
    def test_load_local_gallery_metadata_success(self, tmp_path):
        """Test loading gallery metadata from local file system."""
        from src.command.deploy import load_local_gallery_metadata
        from src.models.photo import GalleryMetadata, GallerySettings, PhotoMetadata, MetadataExifData, MetadataFileData
        
        # Create test metadata file
        prod_dir = tmp_path / "prod" / "pics"
        prod_dir.mkdir(parents=True)
        
        metadata = GalleryMetadata(
            schema_version="1.0",
            generated_at="2024-10-28T10:00:00Z",
            collection="test-collection",
            settings=GallerySettings(timestamp_offset_hours=-4),
            photos=[]
        )
        
        metadata_file = prod_dir / "gallery-metadata.json"
        import json
        metadata_file.write_text(json.dumps(metadata.to_dict()))
        
        # Test loading
        result = load_local_gallery_metadata(prod_dir)
        
        assert isinstance(result, GalleryMetadata)
        assert result.schema_version == "1.0"
        assert result.collection == "test-collection"
        assert result.settings.timestamp_offset_hours == -4
    
    def test_load_local_gallery_metadata_file_not_found(self, tmp_path):
        """Test loading gallery metadata when file doesn't exist."""
        from src.command.deploy import load_local_gallery_metadata
        
        prod_dir = tmp_path / "prod" / "pics"
        prod_dir.mkdir(parents=True)
        
        with pytest.raises(FileNotFoundError):
            load_local_gallery_metadata(prod_dir)
    
    def test_load_local_gallery_metadata_invalid_json(self, tmp_path):
        """Test loading gallery metadata with invalid JSON."""
        from src.command.deploy import load_local_gallery_metadata
        
        prod_dir = tmp_path / "prod" / "pics"
        prod_dir.mkdir(parents=True)
        
        metadata_file = prod_dir / "gallery-metadata.json"
        metadata_file.write_text("invalid json content")
        
        with pytest.raises(json.JSONDecodeError):
            load_local_gallery_metadata(prod_dir)


class TestDeployCommandCORSValidation:
    """Test deploy command CORS validation and early exit behavior."""
    
    def test_deploy_exits_early_when_cors_not_configured(self, tmp_path):
        """Test deploy command exits early when CORS is not configured and --setup-cors not provided."""
        from src.command.deploy import deploy
        from click.testing import CliRunner
        
        # Create minimal directory structure
        prod_dir = tmp_path / "prod" / "pics"
        prod_dir.mkdir(parents=True)
        
        runner = CliRunner()
        
        with patch('src.command.deploy.validate_s3_config', return_value=(True, "")):
            with patch('src.command.deploy.get_s3_client') as mock_get_client:
                mock_client = Mock()
                mock_get_client.return_value = mock_client
                
                with patch('src.command.deploy.examine_bucket_cors') as mock_cors:
                    # Mock CORS as not configured
                    mock_cors.return_value = {
                        'success': True,
                        'configured': False,
                        'needs_update': True
                    }
                    
                    with patch.dict(sys.modules, {'settings': Mock(
                        BASE_DIR=tmp_path,
                        S3_PUBLIC_BUCKET="test-bucket",
                        S3_PUBLIC_ENDPOINT="https://s3.example.com",
                        S3_PUBLIC_ACCESS_KEY="test-key",
                        S3_PUBLIC_SECRET_KEY="test-secret",
                        S3_PUBLIC_REGION="us-east-1"
                    )}):
                        result = runner.invoke(deploy, ['--source', str(prod_dir)])
                        
                        assert result.exit_code == 1
                        assert "CORS Status: Not configured for web access" in result.output
                        assert "Deployment aborted: CORS configuration required for web access" in result.output
                        assert "Use --setup-cors to configure CORS" in result.output
    
    def test_deploy_exits_early_when_cors_needs_update(self, tmp_path):
        """Test deploy command exits early when CORS needs updating and --setup-cors not provided."""
        from src.command.deploy import deploy
        from click.testing import CliRunner
        
        prod_dir = tmp_path / "prod" / "pics"
        prod_dir.mkdir(parents=True)
        
        runner = CliRunner()
        
        with patch('src.command.deploy.validate_s3_config', return_value=(True, "")):
            with patch('src.command.deploy.get_s3_client') as mock_get_client:
                mock_client = Mock()
                mock_get_client.return_value = mock_client
                
                with patch('src.command.deploy.examine_bucket_cors') as mock_cors:
                    # Mock CORS as configured but needing update
                    mock_cors.return_value = {
                        'success': True,
                        'configured': True,
                        'needs_update': True
                    }
                    
                    with patch.dict(sys.modules, {'settings': Mock(
                        BASE_DIR=tmp_path,
                        S3_PUBLIC_BUCKET="test-bucket",
                        S3_PUBLIC_ENDPOINT="https://s3.example.com",
                        S3_PUBLIC_ACCESS_KEY="test-key",
                        S3_PUBLIC_SECRET_KEY="test-secret",
                        S3_PUBLIC_REGION="us-east-1"
                    )}):
                        result = runner.invoke(deploy, ['--source', str(prod_dir)])
                        
                        assert result.exit_code == 1
                        assert "CORS Status: Configured but rules need updating" in result.output
                        assert "Deployment aborted: CORS configuration required for web access" in result.output
                        assert "Use --setup-cors to update CORS rules" in result.output
    
    def test_deploy_continues_when_cors_properly_configured(self, tmp_path):
        """Test deploy command continues when CORS is properly configured."""
        from src.command.deploy import deploy
        from click.testing import CliRunner
        
        prod_dir = tmp_path / "prod" / "pics"
        prod_dir.mkdir(parents=True)
        
        runner = CliRunner()
        
        with patch('src.command.deploy.validate_s3_config', return_value=(True, "")):
            with patch('src.command.deploy.get_s3_client') as mock_get_client:
                mock_client = Mock()
                mock_get_client.return_value = mock_client
                
                with patch('src.command.deploy.examine_bucket_cors') as mock_cors:
                    # Mock CORS as properly configured
                    mock_cors.return_value = {
                        'success': True,
                        'configured': True,
                        'needs_update': False
                    }
                    
                    with patch('src.command.deploy.deploy_directory_to_s3') as mock_deploy:
                        mock_deploy.return_value = {
                            'success': True,
                            'uploaded_files': 5,
                            'skipped_files': 0,
                            'total_files': 5
                        }
                        
                        with patch.dict(sys.modules, {'settings': Mock(
                            BASE_DIR=tmp_path,
                            S3_PUBLIC_BUCKET="test-bucket",
                            S3_PUBLIC_ENDPOINT="https://s3.example.com",
                            S3_PUBLIC_ACCESS_KEY="test-key",
                            S3_PUBLIC_SECRET_KEY="test-secret",
                            S3_PUBLIC_REGION="us-east-1"
                        )}):
                            result = runner.invoke(deploy, ['--source', str(prod_dir)])
                            
                            # Should not exit early - deployment continues
                            assert "CORS Status: Configured correctly for web access" in result.output
                            assert "Deployment aborted" not in result.output
    
    def test_deploy_configures_cors_when_setup_cors_flag_provided(self, tmp_path):
        """Test deploy command configures CORS when --setup-cors flag is provided."""
        from src.command.deploy import deploy
        from click.testing import CliRunner
        
        prod_dir = tmp_path / "prod" / "pics"
        prod_dir.mkdir(parents=True)
        
        runner = CliRunner()
        
        with patch('src.command.deploy.validate_s3_config', return_value=(True, "")):
            with patch('src.command.deploy.get_s3_client') as mock_get_client:
                mock_client = Mock()
                mock_get_client.return_value = mock_client
                
                with patch('src.command.deploy.examine_bucket_cors') as mock_cors:
                    # Mock CORS as not configured
                    mock_cors.return_value = {
                        'success': True,
                        'configured': False,
                        'needs_update': True
                    }
                    
                    with patch('src.command.deploy.configure_bucket_cors') as mock_configure:
                        mock_configure.return_value = {'success': True}
                        
                        with patch('src.command.deploy.deploy_directory_to_s3') as mock_deploy:
                            mock_deploy.return_value = {
                                'success': True,
                                'uploaded_files': 5,
                                'skipped_files': 0,
                                'total_files': 5
                            }
                            
                            with patch.dict(sys.modules, {'settings': Mock(
                                BASE_DIR=tmp_path,
                                S3_PUBLIC_BUCKET="test-bucket",
                                S3_PUBLIC_ENDPOINT="https://s3.example.com",
                                S3_PUBLIC_ACCESS_KEY="test-key",
                                S3_PUBLIC_SECRET_KEY="test-secret",
                                S3_PUBLIC_REGION="us-east-1"
                            )}):
                                result = runner.invoke(deploy, ['--source', str(prod_dir), '--setup-cors'])
                                
                                # Should configure CORS and continue deployment
                                assert "Configuring CORS rules..." in result.output
                                assert "CORS Status: Configured successfully" in result.output
                                assert "Deployment aborted" not in result.output
                                mock_configure.assert_called_once()
    
    def test_deploy_exits_when_cors_examination_fails(self, tmp_path):
        """Test deploy command exits when CORS examination fails."""
        from src.command.deploy import deploy
        from click.testing import CliRunner
        
        prod_dir = tmp_path / "prod" / "pics"
        prod_dir.mkdir(parents=True)
        
        runner = CliRunner()
        
        with patch('src.command.deploy.validate_s3_config', return_value=(True, "")):
            with patch('src.command.deploy.get_s3_client') as mock_get_client:
                mock_client = Mock()
                mock_get_client.return_value = mock_client
                
                with patch('src.command.deploy.examine_bucket_cors') as mock_cors:
                    # Mock CORS examination failure
                    mock_cors.return_value = {
                        'success': False,
                        'error': 'Access denied to bucket'
                    }
                    
                    with patch.dict(sys.modules, {'settings': Mock(
                        BASE_DIR=tmp_path,
                        S3_PUBLIC_BUCKET="test-bucket",
                        S3_PUBLIC_ENDPOINT="https://s3.example.com",
                        S3_PUBLIC_ACCESS_KEY="test-key",
                        S3_PUBLIC_SECRET_KEY="test-secret",
                        S3_PUBLIC_REGION="us-east-1"
                    )}):
                        result = runner.invoke(deploy, ['--source', str(prod_dir)])
                        
                        assert result.exit_code == 1
                        assert "CORS Status: Could not examine CORS: Access denied to bucket" in result.output
                        assert "Deployment aborted: Unable to verify bucket configuration" in result.output