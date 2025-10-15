"""Tests for upload-photos command."""
import pytest
import sys
from pathlib import Path
from unittest.mock import patch, Mock
from click.testing import CliRunner
from moto import mock_aws
import boto3

from src.command.upload_photos import upload_photos, validate_s3_config


class TestValidateS3Config:
    """Test S3 configuration validation."""
    
    def test_validate_complete_config(self):
        """Test validation with all required settings."""
        settings = Mock()
        settings.S3_PUBLIC_ENDPOINT = 'eu-central-1.s3.hetznerobjects.com'
        settings.S3_PUBLIC_ACCESS_KEY = 'test_key'
        settings.S3_PUBLIC_SECRET_KEY = 'test_secret'
        settings.S3_PUBLIC_BUCKET = 'test-bucket'
        settings.S3_PUBLIC_REGION = 'eu-central-1'
        
        is_valid, error_msg = validate_s3_config(settings)
        assert is_valid
        assert error_msg == ""
    
    def test_validate_missing_endpoint(self):
        """Test validation with missing endpoint."""
        settings = Mock()
        settings.S3_PUBLIC_ENDPOINT = None
        settings.S3_PUBLIC_ACCESS_KEY = 'test_key'
        settings.S3_PUBLIC_SECRET_KEY = 'test_secret'
        settings.S3_PUBLIC_BUCKET = 'test-bucket'
        settings.S3_PUBLIC_REGION = 'eu-central-1'
        
        is_valid, error_msg = validate_s3_config(settings)
        assert not is_valid
        assert 'S3_PUBLIC_ENDPOINT' in error_msg
    
    def test_validate_multiple_missing(self):
        """Test validation with multiple missing settings."""
        settings = Mock()
        settings.S3_PUBLIC_ENDPOINT = None
        settings.S3_PUBLIC_ACCESS_KEY = None
        settings.S3_PUBLIC_SECRET_KEY = 'test_secret'
        settings.S3_PUBLIC_BUCKET = 'test-bucket'
        settings.S3_PUBLIC_REGION = 'eu-central-1'
        
        is_valid, error_msg = validate_s3_config(settings)
        assert not is_valid
        assert 'S3_PUBLIC_ENDPOINT' in error_msg
        assert 'S3_PUBLIC_ACCESS_KEY' in error_msg


@pytest.fixture
def mock_settings():
    """Create mock settings for testing."""
    settings = Mock()
    settings.S3_PUBLIC_ENDPOINT = 's3.amazonaws.com'
    settings.S3_PUBLIC_ACCESS_KEY = 'test_key'
    settings.S3_PUBLIC_SECRET_KEY = 'test_secret'
    settings.S3_PUBLIC_BUCKET = 'test-bucket'
    settings.S3_PUBLIC_REGION = 'us-east-1'
    settings.BASE_DIR = Path('/tmp')
    return settings


@pytest.fixture
def processed_dir_with_files(tmp_path):
    """Create a prod/pics directory structure with test files."""
    processed = tmp_path / "prod" / "pics"
    (processed / "full").mkdir(parents=True)
    (processed / "web").mkdir(parents=True)
    (processed / "thumb").mkdir(parents=True)
    
    # Create test files
    (processed / "full" / "photo1.jpg").write_text("full1")
    (processed / "full" / "photo2.jpg").write_text("full2")
    (processed / "web" / "photo1.jpg").write_text("web1")
    (processed / "web" / "photo2.jpg").write_text("web2")
    (processed / "thumb" / "photo1.webp").write_text("thumb1")
    (processed / "thumb" / "photo2.webp").write_text("thumb2")
    
    return processed


class TestUploadPhotosCommand:
    """Test upload-photos command."""
    
    def test_missing_s3_config(self):
        """Test command fails with missing S3 configuration."""
        runner = CliRunner()
        
        with patch.dict(sys.modules, {'settings': Mock()}):
            mock_settings_module = sys.modules['settings']
            mock_settings_module.S3_PUBLIC_ENDPOINT = None
            
            result = runner.invoke(upload_photos)
            
            assert result.exit_code == 1
            assert "Missing required S3 settings" in result.output
    
    def test_source_dir_not_exists(self, mock_settings):
        """Test command fails when source directory doesn't exist."""
        runner = CliRunner()
        
        with patch.dict(sys.modules, {'settings': mock_settings}):
            result = runner.invoke(upload_photos, ['--source', '/nonexistent'])
            
            # Click returns exit code 2 for path validation errors
            assert result.exit_code == 2
            assert "does not exist" in result.output
    
    @mock_aws
    def test_upload_success(self, mock_settings, processed_dir_with_files):
        """Test successful upload."""
        runner = CliRunner()
        
        # Create S3 bucket
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='test-bucket')
        
        mock_settings.BASE_DIR = processed_dir_with_files.parent.parent
        
        with patch.dict(sys.modules, {'settings': mock_settings}):
            result = runner.invoke(upload_photos)
            
            assert result.exit_code == 0
            assert "Uploading photos to S3..." in result.output
            assert "Upload completed successfully!" in result.output
            assert "Total files: 6" in result.output
    
    @mock_aws
    def test_upload_with_custom_source(self, mock_settings, processed_dir_with_files):
        """Test upload with custom source directory."""
        runner = CliRunner()
        
        # Create S3 bucket
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='test-bucket')
        
        with patch.dict(sys.modules, {'settings': mock_settings}):
            result = runner.invoke(upload_photos, [
                '--source', str(processed_dir_with_files)
            ])
            
            assert result.exit_code == 0
            assert str(processed_dir_with_files) in result.output
    
    @mock_aws
    def test_upload_dry_run(self, mock_settings, processed_dir_with_files):
        """Test dry run mode."""
        runner = CliRunner()
        
        # Create S3 bucket
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='test-bucket')
        
        mock_settings.BASE_DIR = processed_dir_with_files.parent.parent
        
        with patch.dict(sys.modules, {'settings': mock_settings}):
            result = runner.invoke(upload_photos, ['--dry-run'])
            
            assert result.exit_code == 0
            assert "[DRY RUN]" in result.output
            assert "Dry run - no files will be uploaded" in result.output
            
            # Verify no files were uploaded
            response = s3.list_objects_v2(Bucket='test-bucket')
            assert 'Contents' not in response
    
    @mock_aws
    def test_upload_with_prefix(self, mock_settings, processed_dir_with_files):
        """Test upload with S3 prefix."""
        runner = CliRunner()
        
        # Create S3 bucket
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='test-bucket')
        
        mock_settings.BASE_DIR = processed_dir_with_files.parent.parent
        
        with patch.dict(sys.modules, {'settings': mock_settings}):
            result = runner.invoke(upload_photos, ['--prefix', 'wedding-2024'])
            
            assert result.exit_code == 0
            assert "Prefix: wedding-2024" in result.output
            
            # Verify files have correct prefix
            response = s3.list_objects_v2(Bucket='test-bucket')
            for obj in response.get('Contents', []):
                assert obj['Key'].startswith('wedding-2024/')
    
    def test_upload_empty_directory(self, mock_settings, tmp_path):
        """Test upload with empty directory."""
        runner = CliRunner()
        
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()
        # Create prod/pics structure
        empty_pics = empty_dir / "prod" / "pics"
        empty_pics.mkdir(parents=True)
        mock_settings.BASE_DIR = empty_dir
        
        with patch.dict(sys.modules, {'settings': mock_settings}):
            result = runner.invoke(upload_photos)
            
            assert result.exit_code == 0
            assert "No files found" in result.output
    
    @mock_aws
    def test_upload_with_progress(self, mock_settings, processed_dir_with_files):
        """Test upload with progress display."""
        runner = CliRunner()
        
        # Create S3 bucket
        s3 = boto3.client('s3', region_name='us-east-1')
        s3.create_bucket(Bucket='test-bucket')
        
        mock_settings.BASE_DIR = processed_dir_with_files.parent.parent
        
        with patch.dict(sys.modules, {'settings': mock_settings}):
            result = runner.invoke(upload_photos, ['--progress'])
            
            assert result.exit_code == 0
            # Progress output might not show in test environment,
            # but command should complete successfully
    
    @mock_aws
    def test_upload_handles_errors(self, mock_settings, processed_dir_with_files):
        """Test upload handles S3 errors gracefully."""
        runner = CliRunner()
        
        mock_settings.BASE_DIR = processed_dir_with_files.parent.parent
        
        # Don't create bucket to simulate error
        with patch.dict(sys.modules, {'settings': mock_settings}):
            result = runner.invoke(upload_photos)
            
            # Should handle error gracefully
            assert result.exit_code == 1