"""Integration tests for enhanced deploy command using Phase 4 deployment orchestration."""
import pytest
import json
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from click.testing import CliRunner

from src.command.deploy import deploy
from src.models.photo import GalleryMetadata, PhotoMetadata, MetadataExifData, MetadataFileData


@pytest.fixture
def sample_gallery_metadata():
    """Create sample gallery metadata for testing."""
    from src.models.photo import GallerySettings
    
    return GalleryMetadata(
        schema_version="1.0",
        generated_at="2024-10-28T10:00:00Z",
        collection="wedding-collection",
        settings=GallerySettings(timestamp_offset_hours=-4),
        photos=[
            PhotoMetadata(
                id="2024-06-15_14-30-45_wedding-ceremony",
                original_path="/src/photos/2024-06-15_14-30-45_wedding-ceremony.jpg",
                exif=MetadataExifData(
                    original_timestamp="2024-06-15T14:30:45",
                    corrected_timestamp="2024-06-15T10:30:45",
                    timezone_original="+00:00",
                    camera={"make": "Canon", "model": "EOS R5"},
                    subsecond=None
                ),
                files=MetadataFileData(
                    full="photos/full/2024-06-15_14-30-45_wedding-ceremony.jpg",
                    web="photos/web/2024-06-15_14-30-45_wedding-ceremony.jpg",
                    thumb="photos/thumb/2024-06-15_14-30-45_wedding-ceremony.webp"
                ),
                file_hash="abc123",
                deployment_file_hash="def456"
            ),
            PhotoMetadata(
                id="2024-06-15_14-32-10_wedding-rings", 
                original_path="/src/photos/2024-06-15_14-32-10_wedding-rings.jpg",
                exif=MetadataExifData(
                    original_timestamp="2024-06-15T14:32:10",
                    corrected_timestamp="2024-06-15T10:32:10",
                    timezone_original="+00:00",
                    camera={"make": "Canon", "model": "EOS R5"},
                    subsecond=None
                ),
                files=MetadataFileData(
                    full="photos/full/2024-06-15_14-32-10_wedding-rings.jpg",
                    web="photos/web/2024-06-15_14-32-10_wedding-rings.jpg",
                    thumb="photos/thumb/2024-06-15_14-32-10_wedding-rings.webp"
                ),
                file_hash="xyz789",
                deployment_file_hash="uvw012"
            )
        ]
    )


class TestDeployCommandIntegration:
    """Integration tests for deploy command using metadata-driven deployment."""
    
    def test_complete_deploy_workflow_with_metadata_comparison(self, tmp_path, sample_gallery_metadata):
        """Test complete deployment workflow using metadata comparison."""
        
        runner = CliRunner()
        
        # Set up directory structure
        prod_dir = tmp_path / "prod" / "pics"
        prod_dir.mkdir(parents=True)
        
        # Create gallery-metadata.json
        metadata_file = prod_dir / "gallery-metadata.json"
        metadata_file.write_text(json.dumps(sample_gallery_metadata.to_dict()))
        
        # Create sample photo files
        for photo in sample_gallery_metadata.photos:
            for variant in ['full', 'web', 'thumb']:
                photo_path = prod_dir / getattr(photo.files, variant)
                photo_path.parent.mkdir(parents=True, exist_ok=True)
                photo_path.write_bytes(b"fake image data")
        
        mock_settings = Mock()
        mock_settings.BASE_DIR = tmp_path
        mock_settings.S3_PUBLIC_BUCKET = "test-bucket"
        mock_settings.S3_PUBLIC_ENDPOINT = "https://s3.example.com"
        mock_settings.S3_PUBLIC_ACCESS_KEY = "test-key"
        mock_settings.S3_PUBLIC_SECRET_KEY = "test-secret"
        mock_settings.S3_PUBLIC_REGION = "us-east-1"
        
        with patch.dict(sys.modules, {'settings': mock_settings}):
            with patch('src.command.deploy.validate_s3_config', return_value=(True, "")):
                with patch('src.command.deploy.get_s3_client') as mock_get_client:
                    mock_client = Mock()
                    mock_get_client.return_value = mock_client
                    
                    with patch('src.command.deploy.deploy_gallery_metadata') as mock_deploy:
                        mock_deploy.return_value = {
                            'success': True,
                            'photos_uploaded': 2,
                            'metadata_uploaded': True,
                            'message': 'Deployment completed successfully'
                        }
                        
                        result = runner.invoke(deploy)
                        
                        # Debug output for failed test
                        if result.exit_code != 0:
                            print(f"Exit code: {result.exit_code}")
                            print(f"Output: {result.output}")
                            print(f"Exception: {result.exception}")
                        
                        assert result.exit_code == 0
                        assert "Deployment completed successfully" in result.output
                        
                        # Verify deploy_gallery_metadata was called with correct parameters
                        mock_deploy.assert_called_once()
                        args, kwargs = mock_deploy.call_args
                        assert kwargs['client'] == mock_client
                        assert kwargs['bucket'] == "test-bucket"
                        assert isinstance(kwargs['local_metadata'], GalleryMetadata)
                        assert kwargs['prod_dir'] == prod_dir
                        assert kwargs['dry_run'] is False
    
    def test_dry_run_shows_deployment_plan(self, tmp_path, sample_gallery_metadata):
        """Test --dry-run option shows deployment plan without uploading."""
        
        runner = CliRunner()
        
        # Set up test data
        prod_dir = tmp_path / "prod" / "pics"
        prod_dir.mkdir(parents=True)
        
        metadata_file = prod_dir / "gallery-metadata.json"
        metadata_file.write_text(json.dumps(sample_gallery_metadata.to_dict()))
        
        mock_settings = Mock()
        mock_settings.BASE_DIR = tmp_path
        mock_settings.S3_PUBLIC_BUCKET = "test-bucket"
        
        deployment_plan = {
            'upload': [sample_gallery_metadata.photos[0]],  # One new photo
            'delete': [],
            'unchanged': [sample_gallery_metadata.photos[1]]  # One unchanged photo
        }
        
        with patch.dict(sys.modules, {'settings': mock_settings}):
            with patch('src.command.deploy.validate_s3_config', return_value=(True, "")):
                with patch('src.command.deploy.get_s3_client'):
                    with patch('src.command.deploy.deploy_gallery_metadata') as mock_deploy:
                        mock_deploy.return_value = {
                            'success': True,
                            'dry_run': True,
                            'plan': deployment_plan,
                            'message': 'Dry run completed'
                        }
                        
                        result = runner.invoke(deploy, ['--dry-run', '--photos-only'])
                        
                        assert result.exit_code == 0
                        assert "DRY RUN" in result.output
                        assert "Photos to upload: 1" in result.output
                        assert "Photos unchanged: 1" in result.output
                        assert "Dry run completed - no files were uploaded" in result.output
                        
                        # Verify dry_run was passed correctly
                        mock_deploy.assert_called_once()
                        args, kwargs = mock_deploy.call_args
                        assert kwargs['dry_run'] is True
    
    def test_force_deployment_ignores_hash_comparison(self, tmp_path, sample_gallery_metadata):
        """Test --force option uploads all photos ignoring hash comparison."""
        
        runner = CliRunner()
        
        # Set up test data similar to previous tests
        prod_dir = tmp_path / "prod" / "pics"
        prod_dir.mkdir(parents=True)
        
        metadata_file = prod_dir / "gallery-metadata.json"
        metadata_file.write_text(json.dumps(sample_gallery_metadata.to_dict()))
        
        mock_settings = Mock()
        mock_settings.BASE_DIR = tmp_path
        mock_settings.S3_PUBLIC_BUCKET = "test-bucket"
        
        with patch.dict(sys.modules, {'settings': mock_settings}):
            with patch('src.command.deploy.validate_s3_config', return_value=(True, "")):
                with patch('src.command.deploy.get_s3_client'):
                    with patch('src.command.deploy.deploy_gallery_metadata') as mock_deploy:
                        mock_deploy.return_value = {
                            'success': True,
                            'photos_uploaded': 2,
                            'metadata_uploaded': True,
                            'message': 'Force deployment completed'
                        }
                        
                        result = runner.invoke(deploy, ['--force', '--photos-only'])
                        
                        assert result.exit_code == 0
                        # Verify force mode was used (implementation needed)
    
    def test_progress_reporting(self, tmp_path, sample_gallery_metadata):
        """Test --progress option shows detailed progress during upload."""
        # TODO: This test requires --progress option implementation
        pytest.skip("--progress option not yet implemented")
        
        runner = CliRunner()
        
        result = runner.invoke(deploy, ['--progress'])
        
        assert result.exit_code == 0
        # Should show progress indicators during upload
    
    def test_user_confirmation_for_deployment_plans(self, tmp_path):
        """Test user confirmation prompt for deployment plans."""
        # TODO: This test requires user confirmation implementation
        pytest.skip("User confirmation not yet implemented")
        
        runner = CliRunner()
        
        # Test with 'y' input to confirm
        result = runner.invoke(deploy, input='y\n')
        
        assert result.exit_code == 0
        assert "proceed with deployment" in result.output.lower() or "confirm" in result.output.lower()
    
    def test_error_handling_partial_upload_recovery(self, tmp_path):
        """Test error handling and partial upload recovery scenarios."""
        # TODO: This test requires enhanced error handling implementation
        pytest.skip("Enhanced error handling not yet implemented")
        
        runner = CliRunner()
        
        # Simulate partial upload failure and recovery
        # Should handle S3 errors gracefully and allow retry
    
    def test_settings_aware_deployment_timezone_changes(self, tmp_path):
        """Test deployment detects timezone setting changes and triggers hash recalculation."""
        # TODO: This test requires settings-aware deployment implementation
        pytest.skip("Settings-aware deployment not yet implemented")
        
        runner = CliRunner()
        
        # Test that changing TARGET_TIMEZONE_OFFSET_HOURS triggers redeployment
        # Even if original file hasn't changed
    
    def test_atomic_operations_metadata_last_upload(self, tmp_path):
        """Test atomic operations ensure metadata is uploaded last for consistency."""
        # TODO: This test requires atomic operations verification
        pytest.skip("Atomic operations verification not yet implemented")
        
        runner = CliRunner()
        
        # Test that photos are uploaded before metadata
        # Verify metadata reflects actual remote state
    
    def test_streaming_exif_modification_during_upload(self, tmp_path):
        """Test EXIF modification happens during upload without local storage."""
        # TODO: This test requires EXIF streaming integration
        pytest.skip("EXIF streaming integration not yet implemented")
        
        runner = CliRunner()
        
        # Test that EXIF is modified in memory during S3 upload
        # Verify no temporary files are created locally