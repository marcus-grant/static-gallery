"""Tests for deployment service functions."""
import pytest
import json
from pathlib import Path
from unittest.mock import Mock, patch
from botocore.exceptions import ClientError

from src.services.deployment import (
    deploy_directory_to_s3,
    download_remote_metadata,
    generate_deployment_plan,
    verify_s3_state,
    deploy_gallery_metadata
)
from src.models.photo import GalleryMetadata, PhotoMetadata, MetadataExifData, MetadataFileData, GallerySettings


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


class TestDownloadRemoteMetadata:
    """Test download_remote_metadata function."""
    
    def test_download_existing_metadata(self):
        """Test downloading existing metadata from S3."""
        mock_client = Mock()
        mock_response = {
            'Body': Mock()
        }
        
        metadata_json = {
            "schema_version": "1.0",
            "generated_at": "2024-10-28T12:00:00Z",
            "collection": "wedding",
            "settings": {"timestamp_offset_hours": -4},
            "photos": [
                {
                    "id": "wedding-001",
                    "original_path": "pics-full/IMG_001.jpg",
                    "file_hash": "abc123",
                    "deployment_file_hash": "def456",
                    "exif": {
                        "original_timestamp": "2024-08-10T18:30:45",
                        "corrected_timestamp": "2024-08-10T14:30:45",
                        "timezone_original": "+00:00",
                        "camera": {"make": "Canon", "model": "EOS R5"},
                        "subsecond": 123
                    },
                    "files": {
                        "full": "full/wedding-001.jpg",
                        "web": "web/wedding-001.jpg",
                        "thumb": "wedding-001.webp"
                    }
                }
            ]
        }
        
        mock_response['Body'].read.return_value = json.dumps(metadata_json).encode()
        mock_client.get_object.return_value = mock_response
        
        result = download_remote_metadata(mock_client, "test-bucket", "gallery-metadata.json")
        
        assert result is not None
        assert result.collection == "wedding"
        assert len(result.photos) == 1
        assert result.photos[0].id == "wedding-001"
        assert result.photos[0].deployment_file_hash == "def456"
        
        mock_client.get_object.assert_called_once_with(
            Bucket="test-bucket",
            Key="gallery-metadata.json"
        )
    
    def test_download_missing_metadata(self):
        """Test downloading when metadata doesn't exist."""
        mock_client = Mock()
        mock_client.get_object.side_effect = ClientError(
            {'Error': {'Code': 'NoSuchKey'}}, 'GetObject'
        )
        
        result = download_remote_metadata(mock_client, "test-bucket", "gallery-metadata.json")
        
        assert result is None
    
    def test_download_metadata_invalid_json(self):
        """Test handling of invalid JSON in metadata."""
        mock_client = Mock()
        mock_response = {
            'Body': Mock()
        }
        mock_response['Body'].read.return_value = b"invalid json"
        mock_client.get_object.return_value = mock_response
        
        result = download_remote_metadata(mock_client, "test-bucket", "gallery-metadata.json")
        
        assert result is None


class TestGenerateDeploymentPlan:
    """Test generate_deployment_plan function."""
    
    def create_sample_metadata(self, photos_data):
        """Helper to create GalleryMetadata with given photos."""
        photos = []
        for photo_data in photos_data:
            photo = PhotoMetadata(
                id=photo_data["id"],
                original_path=photo_data["original_path"],
                file_hash=photo_data["file_hash"],
                deployment_file_hash=photo_data["deployment_file_hash"],
                exif=MetadataExifData(
                    original_timestamp="2024-08-10T18:30:45",
                    corrected_timestamp="2024-08-10T14:30:45",
                    timezone_original="+00:00",
                    camera={"make": "Canon", "model": "EOS R5"},
                    subsecond=123
                ),
                files=MetadataFileData(
                    full=f"full/{photo_data['id']}.jpg",
                    web=f"web/{photo_data['id']}.jpg",
                    thumb=f"thumb/{photo_data['id']}.webp"
                )
            )
            photos.append(photo)
        
        return GalleryMetadata(
            schema_version="1.0",
            generated_at="2024-10-28T12:00:00Z",
            collection="wedding",
            settings=GallerySettings(timestamp_offset_hours=-4),
            photos=photos
        )
    
    def test_plan_with_new_photos(self):
        """Test deployment plan when local has new photos."""
        local_photos = [
            {"id": "photo-001", "original_path": "IMG_001.jpg", "file_hash": "abc123", "deployment_file_hash": "def456"},
            {"id": "photo-002", "original_path": "IMG_002.jpg", "file_hash": "ghi789", "deployment_file_hash": "jkl012"}
        ]
        remote_photos = [
            {"id": "photo-001", "original_path": "IMG_001.jpg", "file_hash": "abc123", "deployment_file_hash": "def456"}
        ]
        
        local_metadata = self.create_sample_metadata(local_photos)
        remote_metadata = self.create_sample_metadata(remote_photos)
        
        plan = generate_deployment_plan(local_metadata, remote_metadata)
        
        assert len(plan['upload']) == 1
        assert plan['upload'][0].id == "photo-002"
        assert len(plan['unchanged']) == 1
        assert plan['unchanged'][0].id == "photo-001"
        assert len(plan['delete']) == 0
    
    def test_plan_with_modified_photos(self):
        """Test deployment plan when photos have changed."""
        local_photos = [
            {"id": "photo-001", "original_path": "IMG_001.jpg", "file_hash": "abc123", "deployment_file_hash": "new_hash"}
        ]
        remote_photos = [
            {"id": "photo-001", "original_path": "IMG_001.jpg", "file_hash": "abc123", "deployment_file_hash": "old_hash"}
        ]
        
        local_metadata = self.create_sample_metadata(local_photos)
        remote_metadata = self.create_sample_metadata(remote_photos)
        
        plan = generate_deployment_plan(local_metadata, remote_metadata)
        
        assert len(plan['upload']) == 1
        assert plan['upload'][0].id == "photo-001"
        assert len(plan['unchanged']) == 0
        assert len(plan['delete']) == 0
    
    def test_plan_with_orphaned_remote_photos(self):
        """Test deployment plan when remote has orphaned photos."""
        local_photos = [
            {"id": "photo-001", "original_path": "IMG_001.jpg", "file_hash": "abc123", "deployment_file_hash": "def456"}
        ]
        remote_photos = [
            {"id": "photo-001", "original_path": "IMG_001.jpg", "file_hash": "abc123", "deployment_file_hash": "def456"},
            {"id": "photo-002", "original_path": "IMG_002.jpg", "file_hash": "ghi789", "deployment_file_hash": "jkl012"}
        ]
        
        local_metadata = self.create_sample_metadata(local_photos)
        remote_metadata = self.create_sample_metadata(remote_photos)
        
        plan = generate_deployment_plan(local_metadata, remote_metadata)
        
        assert len(plan['upload']) == 0
        assert len(plan['unchanged']) == 1
        assert len(plan['delete']) == 1
        assert plan['delete'][0] == "photo-002"
    
    def test_plan_with_no_remote_metadata(self):
        """Test deployment plan when no remote metadata exists."""
        local_photos = [
            {"id": "photo-001", "original_path": "IMG_001.jpg", "file_hash": "abc123", "deployment_file_hash": "def456"},
            {"id": "photo-002", "original_path": "IMG_002.jpg", "file_hash": "ghi789", "deployment_file_hash": "jkl012"}
        ]
        
        local_metadata = self.create_sample_metadata(local_photos)
        
        plan = generate_deployment_plan(local_metadata, None)
        
        assert len(plan['upload']) == 2
        assert len(plan['unchanged']) == 0
        assert len(plan['delete']) == 0
    
    def test_plan_with_no_changes(self):
        """Test deployment plan when everything is in sync."""
        photos_data = [
            {"id": "photo-001", "original_path": "IMG_001.jpg", "file_hash": "abc123", "deployment_file_hash": "def456"},
            {"id": "photo-002", "original_path": "IMG_002.jpg", "file_hash": "ghi789", "deployment_file_hash": "jkl012"}
        ]
        
        local_metadata = self.create_sample_metadata(photos_data)
        remote_metadata = self.create_sample_metadata(photos_data)
        
        plan = generate_deployment_plan(local_metadata, remote_metadata)
        
        assert len(plan['upload']) == 0
        assert len(plan['unchanged']) == 2
        assert len(plan['delete']) == 0


class TestVerifyS3State:
    """Test verify_s3_state function."""
    
    def test_verify_with_matching_files(self):
        """Test S3 state verification when files match metadata."""
        mock_client = Mock()
        mock_client.list_objects_v2.return_value = {
            'Contents': [
                {'Key': 'full/photo-001.jpg'},
                {'Key': 'web/photo-001.jpg'},
                {'Key': 'thumb/photo-001.webp'},
                {'Key': 'gallery-metadata.json'}
            ]
        }
        
        photos_data = [
            {"id": "photo-001", "original_path": "IMG_001.jpg", "file_hash": "abc123", "deployment_file_hash": "def456"}
        ]
        metadata = TestGenerateDeploymentPlan().create_sample_metadata(photos_data)
        
        result = verify_s3_state(mock_client, "test-bucket", metadata)
        
        assert result['consistent'] == True
        assert len(result['missing_files']) == 0
        assert len(result['orphaned_files']) == 0
    
    def test_verify_with_missing_files(self):
        """Test S3 state verification when files are missing."""
        mock_client = Mock()
        mock_client.list_objects_v2.return_value = {
            'Contents': [
                {'Key': 'full/photo-001.jpg'},
                {'Key': 'gallery-metadata.json'}
            ]
        }
        
        photos_data = [
            {"id": "photo-001", "original_path": "IMG_001.jpg", "file_hash": "abc123", "deployment_file_hash": "def456"}
        ]
        metadata = TestGenerateDeploymentPlan().create_sample_metadata(photos_data)
        
        result = verify_s3_state(mock_client, "test-bucket", metadata)
        
        assert result['consistent'] == False
        assert 'web/photo-001.jpg' in result['missing_files']
        assert 'thumb/photo-001.webp' in result['missing_files']
    
    def test_verify_with_orphaned_files(self):
        """Test S3 state verification when orphaned files exist."""
        mock_client = Mock()
        mock_client.list_objects_v2.return_value = {
            'Contents': [
                {'Key': 'full/photo-001.jpg'},
                {'Key': 'web/photo-001.jpg'},
                {'Key': 'thumb/photo-001.webp'},
                {'Key': 'full/orphan.jpg'},
                {'Key': 'web/orphan.jpg'},
                {'Key': 'gallery-metadata.json'}
            ]
        }
        
        photos_data = [
            {"id": "photo-001", "original_path": "IMG_001.jpg", "file_hash": "abc123", "deployment_file_hash": "def456"}
        ]
        metadata = TestGenerateDeploymentPlan().create_sample_metadata(photos_data)
        
        result = verify_s3_state(mock_client, "test-bucket", metadata)
        
        assert result['consistent'] == False
        assert 'full/orphan.jpg' in result['orphaned_files']
        assert 'web/orphan.jpg' in result['orphaned_files']


class TestDeployGalleryMetadata:
    """Test deploy_gallery_metadata orchestration function."""
    
    def create_sample_metadata(self, photos_data):
        """Helper to create GalleryMetadata with given photos."""
        photos = []
        for photo_data in photos_data:
            photo = PhotoMetadata(
                id=photo_data["id"],
                original_path=photo_data["original_path"],
                file_hash=photo_data["file_hash"],
                deployment_file_hash=photo_data["deployment_file_hash"],
                exif=MetadataExifData(
                    original_timestamp="2024-08-10T18:30:45",
                    corrected_timestamp="2024-08-10T14:30:45",
                    timezone_original="+00:00",
                    camera={"make": "Canon", "model": "EOS R5"},
                    subsecond=123
                ),
                files=MetadataFileData(
                    full=f"full/{photo_data['id']}.jpg",
                    web=f"web/{photo_data['id']}.jpg",
                    thumb=f"thumb/{photo_data['id']}.webp"
                )
            )
            photos.append(photo)
        
        return GalleryMetadata(
            schema_version="1.0",
            generated_at="2024-10-28T12:00:00Z",
            collection="wedding",
            settings=GallerySettings(timestamp_offset_hours=-4),
            photos=photos
        )
    
    def test_deploy_with_new_photos_uploads_photos_then_metadata(self, tmp_path):
        """Test complete deployment workflow uploads photos first, then metadata."""
        # Setup local metadata
        local_photos = [
            {"id": "photo-001", "original_path": "IMG_001.jpg", "file_hash": "abc123", "deployment_file_hash": "def456"}
        ]
        local_metadata = self.create_sample_metadata(local_photos)
        
        # Setup mock client and remote metadata (empty)
        mock_client = Mock()
        
        # Mock empty remote metadata
        mock_client.get_object.side_effect = ClientError(
            {'Error': {'Code': 'NoSuchKey'}}, 'GetObject'
        )
        
        # Setup production directory structure
        prod_dir = tmp_path / "prod"
        prod_dir.mkdir()
        
        # Create photo files that should be uploaded
        full_dir = prod_dir / "full"
        web_dir = prod_dir / "web"
        thumb_dir = prod_dir / "thumb"
        
        full_dir.mkdir()
        web_dir.mkdir()
        thumb_dir.mkdir()
        
        (full_dir / "photo-001.jpg").write_bytes(b"full photo content")
        (web_dir / "photo-001.jpg").write_bytes(b"web photo content")
        (thumb_dir / "photo-001.webp").write_bytes(b"thumb photo content")
        
        # Create metadata file
        metadata_file = prod_dir / "gallery-metadata.json"
        metadata_file.write_text('{"test": "metadata"}')
        
        # Mock successful uploads
        mock_client.upload_file.return_value = None
        
        result = deploy_gallery_metadata(
            client=mock_client,
            bucket="test-bucket",
            local_metadata=local_metadata,
            prod_dir=prod_dir,
            dry_run=False
        )
        
        assert result['success'] == True
        assert result['photos_uploaded'] == 3  # full, web, thumb
        assert result['metadata_uploaded'] == True
        
        # Verify photos were uploaded before metadata
        upload_calls = mock_client.upload_file.call_args_list
        assert len(upload_calls) == 4  # 3 photos + 1 metadata
        
        # Last call should be metadata
        metadata_call = upload_calls[-1]
        assert 'gallery-metadata.json' in str(metadata_call)
    
    def test_deploy_with_no_changes_skips_upload(self, tmp_path):
        """Test deployment when no changes are needed."""
        photos_data = [
            {"id": "photo-001", "original_path": "IMG_001.jpg", "file_hash": "abc123", "deployment_file_hash": "def456"}
        ]
        
        local_metadata = self.create_sample_metadata(photos_data)
        remote_metadata = self.create_sample_metadata(photos_data)
        
        mock_client = Mock()
        
        # Mock remote metadata exists and matches local
        import json
        mock_response = {'Body': Mock()}
        mock_response['Body'].read.return_value = json.dumps(remote_metadata.to_dict()).encode()
        mock_client.get_object.return_value = mock_response
        
        prod_dir = tmp_path / "prod"
        prod_dir.mkdir()
        
        result = deploy_gallery_metadata(
            client=mock_client,
            bucket="test-bucket",
            local_metadata=local_metadata,
            prod_dir=prod_dir,
            dry_run=False
        )
        
        assert result['success'] == True
        assert result['photos_uploaded'] == 0
        assert result['metadata_uploaded'] == False
        assert 'No changes detected' in result['message']
    
    def test_deploy_dry_run_shows_plan_without_uploading(self, tmp_path):
        """Test dry run mode shows deployment plan without uploading."""
        local_photos = [
            {"id": "photo-001", "original_path": "IMG_001.jpg", "file_hash": "abc123", "deployment_file_hash": "def456"}
        ]
        local_metadata = self.create_sample_metadata(local_photos)
        
        mock_client = Mock()
        mock_client.get_object.side_effect = ClientError(
            {'Error': {'Code': 'NoSuchKey'}}, 'GetObject'
        )
        
        prod_dir = tmp_path / "prod"
        prod_dir.mkdir()
        
        result = deploy_gallery_metadata(
            client=mock_client,
            bucket="test-bucket",
            local_metadata=local_metadata,
            prod_dir=prod_dir,
            dry_run=True
        )
        
        assert result['success'] == True
        assert result['dry_run'] == True
        assert result['plan']['upload_count'] == 1
        assert result['plan']['delete_count'] == 0
        
        # Should not have called upload_file
        mock_client.upload_file.assert_not_called()
    
    def test_deploy_handles_upload_errors_gracefully(self, tmp_path):
        """Test deployment handles upload errors and provides useful feedback."""
        local_photos = [
            {"id": "photo-001", "original_path": "IMG_001.jpg", "file_hash": "abc123", "deployment_file_hash": "def456"}
        ]
        local_metadata = self.create_sample_metadata(local_photos)
        
        mock_client = Mock()
        mock_client.get_object.side_effect = ClientError(
            {'Error': {'Code': 'NoSuchKey'}}, 'GetObject'
        )
        
        # Mock upload failure
        mock_client.upload_file.side_effect = Exception("Upload failed")
        
        prod_dir = tmp_path / "prod"
        prod_dir.mkdir()
        
        # Create photo files
        full_dir = prod_dir / "full"
        full_dir.mkdir()
        (full_dir / "photo-001.jpg").write_bytes(b"content")
        
        result = deploy_gallery_metadata(
            client=mock_client,
            bucket="test-bucket",
            local_metadata=local_metadata,
            prod_dir=prod_dir,
            dry_run=False
        )
        
        assert result['success'] == False
        assert 'Upload failed' in result['error']