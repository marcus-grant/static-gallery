import pytest
from unittest.mock import patch, MagicMock
from botocore.exceptions import NoCredentialsError, ClientError

from src.services.s3_storage import get_s3_client, file_exists_in_s3, upload_file_to_s3, list_bucket_files, upload_directory_to_s3


class TestS3Client:
    """Test S3 client creation functionality."""
    
    def test_get_s3_client_creates_boto3_client(self):
        """Test that get_s3_client creates a boto3 S3 client with correct parameters."""
        # Mock boto3.client to verify it's called with correct parameters
        with patch('src.services.s3_storage.boto3.client') as mock_boto_client:
            mock_s3_client = MagicMock()
            mock_boto_client.return_value = mock_s3_client
            
            # Test basic S3 client creation
            endpoint = 'eu-central-1.s3.hetznerobjects.com'
            access_key = 'test-access-key'
            secret_key = 'test-secret-key'
            region = 'eu-central-1'
            
            result = get_s3_client(endpoint, access_key, secret_key, region)
            
            # Verify boto3.client was called with correct parameters
            mock_boto_client.assert_called_once_with(
                's3',
                endpoint_url=f'https://{endpoint}',
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                region_name=region
            )
            
            # Verify the function returns the boto3 client
            assert result == mock_s3_client


class TestFileExists:
    """Test S3 file existence checking functionality."""
    
    def test_file_exists_in_s3_returns_true_when_file_exists(self):
        """Test that file_exists_in_s3 returns True when file exists in bucket."""
        mock_client = MagicMock()
        # Mock successful head_object call (file exists)
        mock_client.head_object.return_value = {'ContentLength': 12345}
        
        bucket = 'test-bucket'
        key = 'photos/test-photo.jpg'
        
        result = file_exists_in_s3(mock_client, bucket, key)
        
        # Verify head_object was called with correct parameters
        mock_client.head_object.assert_called_once_with(Bucket=bucket, Key=key)
        
        # Verify function returns True when file exists
        assert result is True
    
    def test_file_exists_in_s3_returns_false_when_file_not_found(self):
        """Test that file_exists_in_s3 returns False when file doesn't exist (404)."""
        mock_client = MagicMock()
        # Mock 404 error (file doesn't exist)
        error_response = {'Error': {'Code': '404', 'Message': 'Not Found'}}
        mock_client.head_object.side_effect = ClientError(error_response, 'HeadObject')
        
        bucket = 'test-bucket'
        key = 'photos/nonexistent-photo.jpg'
        
        result = file_exists_in_s3(mock_client, bucket, key)
        
        # Verify head_object was called
        mock_client.head_object.assert_called_once_with(Bucket=bucket, Key=key)
        
        # Verify function returns False when file doesn't exist
        assert result is False


class TestUploadFile:
    """Test S3 file upload functionality."""
    
    def test_upload_file_to_s3_successful_upload(self):
        """Test successful file upload to S3 bucket."""
        from pathlib import Path
        from unittest.mock import mock_open
        
        mock_client = MagicMock()
        # Mock successful upload_file call
        mock_client.upload_file.return_value = None
        
        # Mock file system
        with patch('pathlib.Path.stat') as mock_stat:
            mock_stat.return_value.st_size = 12345
            
            with patch('builtins.open', mock_open(read_data=b'fake file content')):
                with patch('src.services.s3_storage.calculate_file_checksum', return_value='abc123hash'):
                    with patch('src.services.s3_storage.file_exists_in_s3', return_value=False):
                        
                        local_path = Path('/test/photo.jpg')
                        bucket = 'test-bucket'
                        key = 'photos/photo.jpg'
                        
                        result = upload_file_to_s3(mock_client, local_path, bucket, key)
                        
                        # Verify upload_file was called with correct parameters
                        mock_client.upload_file.assert_called_once_with(
                            str(local_path),
                            bucket,
                            key,
                            ExtraArgs={}
                        )
                        
                        # Verify result indicates success
                        assert result['success'] is True
                        assert result['key'] == key
                        assert result['size'] == 12345
                        assert result['checksum'] == 'abc123hash'
                        assert result['error'] is None
    
    def test_upload_file_to_s3_skips_when_file_already_exists(self):
        """Test that upload is skipped when file already exists in S3."""
        from pathlib import Path
        from unittest.mock import mock_open
        
        mock_client = MagicMock()
        
        # Mock file system
        with patch('pathlib.Path.stat') as mock_stat:
            mock_stat.return_value.st_size = 12345
            
            with patch('builtins.open', mock_open(read_data=b'fake file content')):
                with patch('src.services.s3_storage.calculate_file_checksum', return_value='abc123hash'):
                    with patch('src.services.s3_storage.file_exists_in_s3', return_value=True):
                        
                        local_path = Path('/test/photo.jpg')
                        bucket = 'test-bucket'
                        key = 'photos/photo.jpg'
                        
                        result = upload_file_to_s3(mock_client, local_path, bucket, key)
                        
                        # Verify upload_file was NOT called (file already exists)
                        mock_client.upload_file.assert_not_called()
                        
                        # Verify result indicates success but skipped
                        assert result['success'] is True
                        assert result['key'] == key
                        assert result['size'] == 12345
                        assert result['checksum'] == 'abc123hash'
                        assert 'already exists' in result['error']
    
    def test_upload_file_to_s3_handles_any_upload_error(self):
        """Test that ANY upload error is handled gracefully."""
        from pathlib import Path
        from unittest.mock import mock_open
        
        mock_client = MagicMock()
        # Mock upload_file to raise ANY exception
        mock_client.upload_file.side_effect = Exception("Some random upload failure")
        
        # Mock file system
        with patch('pathlib.Path.stat') as mock_stat:
            mock_stat.return_value.st_size = 12345
            
            with patch('builtins.open', mock_open(read_data=b'fake file content')):
                with patch('src.services.s3_storage.calculate_file_checksum', return_value='abc123hash'):
                    with patch('src.services.s3_storage.file_exists_in_s3', return_value=False):
                        
                        local_path = Path('/test/photo.jpg')
                        bucket = 'test-bucket'
                        key = 'photos/photo.jpg'
                        
                        result = upload_file_to_s3(mock_client, local_path, bucket, key)
                        
                        # Verify upload_file was called but failed
                        mock_client.upload_file.assert_called_once()
                        
                        # Verify result indicates failure
                        assert result['success'] is False
                        assert result['key'] == key
                        assert result['size'] == 12345
                        assert result['checksum'] == 'abc123hash'
                        assert 'Upload error' in result['error']
                        assert 'Some random upload failure' in result['error']


class TestListBucketFiles:
    """Test S3 bucket file listing functionality."""
    
    def test_list_bucket_files_returns_file_keys(self):
        """Test that list_bucket_files returns list of S3 object keys."""
        mock_client = MagicMock()
        # Mock successful list_objects_v2 response
        mock_client.list_objects_v2.return_value = {
            'Contents': [
                {'Key': 'photos/photo1.jpg'},
                {'Key': 'photos/photo2.jpg'},
                {'Key': 'photos/thumbnails/thumb1.webp'}
            ]
        }
        
        bucket = 'test-bucket'
        prefix = 'photos/'
        
        result = list_bucket_files(mock_client, bucket, prefix)
        
        # Verify list_objects_v2 was called with correct parameters
        mock_client.list_objects_v2.assert_called_once_with(Bucket=bucket, Prefix=prefix)
        
        # Verify function returns list of keys
        expected_keys = ['photos/photo1.jpg', 'photos/photo2.jpg', 'photos/thumbnails/thumb1.webp']
        assert result == expected_keys
    
    def test_list_bucket_files_returns_empty_list_on_error(self):
        """Test that list_bucket_files returns empty list when bucket access fails."""
        mock_client = MagicMock()
        # Mock list_objects_v2 to raise an exception
        mock_client.list_objects_v2.side_effect = ClientError(
            {'Error': {'Code': 'NoSuchBucket', 'Message': 'The specified bucket does not exist'}},
            'ListObjectsV2'
        )
        
        bucket = 'nonexistent-bucket'
        prefix = 'photos/'
        
        result = list_bucket_files(mock_client, bucket, prefix)
        
        # Verify list_objects_v2 was called
        mock_client.list_objects_v2.assert_called_once_with(Bucket=bucket, Prefix=prefix)
        
        # Verify function returns empty list on error
        assert result == []


class TestUploadDirectory:
    """Test S3 directory upload functionality."""
    
    def test_upload_directory_to_s3_successful_upload(self):
        """Test successful directory upload to S3 bucket."""
        from pathlib import Path
        
        mock_client = MagicMock()
        
        # Mock the directory structure with rglob
        mock_files = [
            Path('/test/photos/photo1.jpg'),
            Path('/test/photos/photo2.jpg'),
            Path('/test/photos/thumbnails/thumb1.webp')
        ]
        
        with patch('pathlib.Path.rglob') as mock_rglob:
            with patch('pathlib.Path.is_file') as mock_is_file:
                with patch('pathlib.Path.stat') as mock_stat:
                    with patch('src.services.s3_storage.upload_file_to_s3') as mock_upload_file:
                        
                        # Setup mocks
                        mock_rglob.return_value = mock_files
                        mock_is_file.return_value = True
                        mock_stat.return_value.st_size = 12345
                        mock_upload_file.return_value = {'success': True, 'error': None}
                        
                        local_dir = Path('/test/photos')
                        bucket = 'test-bucket'
                        prefix = 'gallery/'
                        
                        result = upload_directory_to_s3(mock_client, local_dir, bucket, prefix)
                        
                        # Verify upload_file_to_s3 was called for each file
                        assert mock_upload_file.call_count == 3
                        
                        # Verify result indicates success
                        assert result['success'] is True
                        assert result['total_files'] == 3
                        assert result['uploaded_files'] == 3
                        assert result['failed_files'] == 0
                        assert result['errors'] == []
    
    def test_upload_directory_to_s3_dry_run_skips_upload(self):
        """Test that dry_run=True skips actual upload but counts files."""
        from pathlib import Path
        
        mock_client = MagicMock()
        
        # Mock the directory structure
        mock_files = [
            Path('/test/photos/photo1.jpg'),
            Path('/test/photos/photo2.jpg')
        ]
        
        with patch('pathlib.Path.rglob') as mock_rglob:
            with patch('pathlib.Path.is_file') as mock_is_file:
                with patch('pathlib.Path.stat') as mock_stat:
                    with patch('src.services.s3_storage.upload_file_to_s3') as mock_upload_file:
                        
                        # Setup mocks
                        mock_rglob.return_value = mock_files
                        mock_is_file.return_value = True
                        mock_stat.return_value.st_size = 12345
                        
                        local_dir = Path('/test/photos')
                        bucket = 'test-bucket'
                        prefix = 'gallery/'
                        
                        result = upload_directory_to_s3(mock_client, local_dir, bucket, prefix, dry_run=True)
                        
                        # Verify upload_file_to_s3 was NOT called (dry run)
                        mock_upload_file.assert_not_called()
                        
                        # Verify result shows counts but no actual uploads
                        assert result['success'] is True
                        assert result['total_files'] == 2
                        assert result['uploaded_files'] == 0
                        assert result['failed_files'] == 0
                        assert result['errors'] == []