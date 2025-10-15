"""Tests for deployment service functions."""
import pytest
from pathlib import Path
from unittest.mock import Mock, patch

from src.services.deployment import deploy_directory_to_s3


class TestDeployDirectoryToS3:
    """Test deploy_directory_to_s3 service function."""
    
    def test_deploy_with_required_parameters(self, tmp_path):
        """Test basic deployment with minimum required parameters."""
        # Create test directory structure
        source_dir = tmp_path / "source"
        source_dir.mkdir()
        (source_dir / "file1.txt").write_text("content1")
        (source_dir / "file2.txt").write_text("content2")
        
        mock_client = Mock()
        
        with patch('src.services.deployment.upload_directory_to_s3') as mock_upload:
            mock_upload.return_value = {
                'success': True,
                'total_files': 2,
                'uploaded_files': 2,
                'skipped_files': 0,
                'failed_files': 0,
                'total_size': 16,
                'errors': []
            }
            
            result = deploy_directory_to_s3(
                client=mock_client,
                source_dir=source_dir,
                bucket="test-bucket"
            )
            
            assert result['success'] == True
            assert result['total_files'] == 2
            mock_upload.assert_called_once_with(
                client=mock_client,
                local_dir=source_dir,
                bucket="test-bucket",
                prefix="",
                dry_run=False,
                progress_callback=None
            )
    
    def test_deploy_with_prefix(self, tmp_path):
        """Test deployment with S3 prefix."""
        source_dir = tmp_path / "source"
        source_dir.mkdir()
        (source_dir / "file1.txt").write_text("content")
        
        mock_client = Mock()
        
        with patch('src.services.deployment.upload_directory_to_s3') as mock_upload:
            mock_upload.return_value = {'success': True, 'total_files': 1}
            
            deploy_directory_to_s3(
                client=mock_client,
                source_dir=source_dir,
                bucket="test-bucket",
                prefix="photos"
            )
            
            mock_upload.assert_called_once()
            args, kwargs = mock_upload.call_args
            assert kwargs['prefix'] == "photos"
    
    def test_deploy_dry_run_mode(self, tmp_path):
        """Test deployment in dry-run mode."""
        source_dir = tmp_path / "source"
        source_dir.mkdir()
        (source_dir / "file1.txt").write_text("content")
        
        mock_client = Mock()
        
        with patch('src.services.deployment.upload_directory_to_s3') as mock_upload:
            mock_upload.return_value = {'success': True, 'total_files': 1}
            
            deploy_directory_to_s3(
                client=mock_client,
                source_dir=source_dir,
                bucket="test-bucket",
                dry_run=True
            )
            
            mock_upload.assert_called_once()
            args, kwargs = mock_upload.call_args
            assert kwargs['dry_run'] == True
    
    def test_deploy_with_progress_callback(self, tmp_path):
        """Test deployment with progress callback."""
        source_dir = tmp_path / "source"
        source_dir.mkdir()
        (source_dir / "file1.txt").write_text("content")
        
        mock_client = Mock()
        mock_callback = Mock()
        
        with patch('src.services.deployment.upload_directory_to_s3') as mock_upload:
            mock_upload.return_value = {'success': True, 'total_files': 1}
            
            deploy_directory_to_s3(
                client=mock_client,
                source_dir=source_dir,
                bucket="test-bucket",
                progress_callback=mock_callback
            )
            
            mock_upload.assert_called_once()
            args, kwargs = mock_upload.call_args
            assert kwargs['progress_callback'] == mock_callback
    
    def test_deploy_nonexistent_directory(self):
        """Test deployment fails gracefully with nonexistent directory."""
        mock_client = Mock()
        nonexistent_dir = Path("/nonexistent/path")
        
        result = deploy_directory_to_s3(
            client=mock_client,
            source_dir=nonexistent_dir,
            bucket="test-bucket"
        )
        
        assert result['success'] == False
        assert 'does not exist' in result['error']
    
    def test_deploy_empty_directory(self, tmp_path):
        """Test deployment with empty directory."""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()
        
        mock_client = Mock()
        
        with patch('src.services.deployment.upload_directory_to_s3') as mock_upload:
            mock_upload.return_value = {
                'success': True,
                'total_files': 0,
                'uploaded_files': 0,
                'skipped_files': 0,
                'failed_files': 0,
                'total_size': 0,
                'errors': []
            }
            
            result = deploy_directory_to_s3(
                client=mock_client,
                source_dir=empty_dir,
                bucket="test-bucket"
            )
            
            assert result['success'] == True
            assert result['total_files'] == 0