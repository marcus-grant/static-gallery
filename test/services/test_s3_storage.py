"""Tests for S3 storage operations."""
import pytest
from pathlib import Path
from unittest.mock import Mock
from datetime import datetime
import hashlib
import io
import boto3
from moto import mock_aws
from botocore.exceptions import ClientError
from PIL import Image
import piexif

from src.services.s3_storage import (
    get_s3_client,
    file_exists_in_s3,
    calculate_file_checksum,
    upload_file_to_s3,
    list_bucket_files,
    upload_directory_to_s3,
    modify_exif_in_memory
)


@pytest.fixture
def temp_file(tmp_path):
    """Create a temporary file for testing."""
    file_path = tmp_path / "test_file.jpg"
    file_path.write_text("test content")
    return file_path


@pytest.fixture
def temp_dir_with_files(tmp_path):
    """Create a temporary directory with test files."""
    # Create directory structure
    (tmp_path / "full").mkdir()
    (tmp_path / "web").mkdir()
    (tmp_path / "thumb").mkdir()
    
    # Create test files
    files = [
        tmp_path / "full" / "photo1.jpg",
        tmp_path / "full" / "photo2.jpg",
        tmp_path / "web" / "photo1.jpg",
        tmp_path / "web" / "photo2.jpg",
        tmp_path / "thumb" / "photo1.webp",
        tmp_path / "thumb" / "photo2.webp",
    ]
    
    for file_path in files:
        file_path.write_text(f"content of {file_path.name}")
    
    return tmp_path


@mock_aws
class TestS3Client:
    """Test S3 client creation."""
    
    def test_get_s3_client(self):
        """Test creating an S3 client."""
        client = get_s3_client(
            endpoint="s3.amazonaws.com",
            access_key="test_key",
            secret_key="test_secret",
            region="us-east-1"
        )
        assert client is not None
        assert hasattr(client, 'list_buckets')


@mock_aws
class TestFileExistence:
    """Test file existence checking."""
    
    def setup_method(self, method):
        """Set up test bucket and client."""
        self.client = boto3.client('s3', region_name='us-east-1')
        self.bucket_name = 'test-bucket'
        self.client.create_bucket(Bucket=self.bucket_name)
    
    def test_file_exists_when_present(self):
        """Test file_exists_in_s3 returns True when file exists."""
        # Put a test object
        self.client.put_object(
            Bucket=self.bucket_name,
            Key='test-file.jpg',
            Body=b'test content'
        )
        
        assert file_exists_in_s3(self.client, self.bucket_name, 'test-file.jpg')
    
    def test_file_exists_when_absent(self):
        """Test file_exists_in_s3 returns False when file doesn't exist."""
        assert not file_exists_in_s3(self.client, self.bucket_name, 'nonexistent.jpg')
    
    def test_file_exists_with_invalid_bucket(self):
        """Test file_exists_in_s3 raises error with invalid bucket."""
        with pytest.raises(ClientError):
            file_exists_in_s3(self.client, 'nonexistent-bucket', 'test.jpg')


class TestChecksum:
    """Test file checksum calculation."""
    
    def test_calculate_file_checksum(self, temp_file):
        """Test SHA256 checksum calculation."""
        checksum = calculate_file_checksum(temp_file)
        # SHA256 of "test content"
        expected = "6ae8a75555209fd6c44157c0aed8016e763ff435a19cf186f76863140143ff72"
        assert checksum == expected
    
    def test_calculate_checksum_empty_file(self, tmp_path):
        """Test checksum of empty file."""
        empty_file = tmp_path / "empty.txt"
        empty_file.write_text("")
        checksum = calculate_file_checksum(empty_file)
        # SHA256 of empty string
        expected = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        assert checksum == expected


@mock_aws
class TestFileUpload:
    """Test single file upload operations."""
    
    def setup_method(self, method):
        """Set up test bucket and client."""
        self.client = boto3.client('s3', region_name='us-east-1')
        self.bucket_name = 'test-bucket'
        self.client.create_bucket(Bucket=self.bucket_name)
    
    def test_upload_file_success(self, temp_file):
        """Test successful file upload."""
        result = upload_file_to_s3(
            self.client,
            temp_file,
            self.bucket_name,
            'uploads/test.jpg'
        )
        
        assert result['success']
        assert result['key'] == 'uploads/test.jpg'
        assert result['size'] == len("test content")
        assert result['checksum'] is not None
        assert result['error'] is None
        
        # Verify file was uploaded
        response = self.client.list_objects_v2(Bucket=self.bucket_name)
        assert len(response['Contents']) == 1
        assert response['Contents'][0]['Key'] == 'uploads/test.jpg'
    
    def test_upload_file_already_exists(self, temp_file):
        """Test upload when file already exists (should skip)."""
        # Upload once
        upload_file_to_s3(self.client, temp_file, self.bucket_name, 'test.jpg')
        
        # Upload again
        result = upload_file_to_s3(
            self.client,
            temp_file,
            self.bucket_name,
            'test.jpg'
        )
        
        assert result['success']
        assert 'already exists' in result['error']
    
    def test_upload_file_with_progress_callback(self, temp_file):
        """Test upload with progress callback."""
        progress_calls = []
        
        def progress_callback(bytes_uploaded):
            progress_calls.append(bytes_uploaded)
        
        result = upload_file_to_s3(
            self.client,
            temp_file,
            self.bucket_name,
            'test.jpg',
            progress_callback=progress_callback
        )
        
        assert result['success']
        # Progress callback should be called at least once
        assert len(progress_calls) > 0
    
    def test_upload_file_invalid_bucket(self, temp_file):
        """Test upload to invalid bucket."""
        result = upload_file_to_s3(
            self.client,
            temp_file,
            'nonexistent-bucket',
            'test.jpg'
        )
        
        assert not result['success']
        assert 'Upload error' in result['error']


@mock_aws
class TestListFiles:
    """Test listing bucket files."""
    
    def setup_method(self, method):
        """Set up test bucket with files."""
        self.client = boto3.client('s3', region_name='us-east-1')
        self.bucket_name = 'test-bucket'
        self.client.create_bucket(Bucket=self.bucket_name)
        
        # Add test files
        test_files = [
            'photos/full/img1.jpg',
            'photos/full/img2.jpg',
            'photos/thumb/img1.webp',
            'other/file.txt'
        ]
        
        for key in test_files:
            self.client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=b'test'
            )
    
    def test_list_all_files(self):
        """Test listing all files in bucket."""
        files = list_bucket_files(self.client, self.bucket_name)
        assert len(files) == 4
    
    def test_list_files_with_prefix(self):
        """Test listing files with prefix."""
        files = list_bucket_files(self.client, self.bucket_name, 'photos/')
        assert len(files) == 3
        assert all(f.startswith('photos/') for f in files)
    
    def test_list_files_empty_bucket(self):
        """Test listing files in empty bucket."""
        empty_bucket = 'empty-bucket'
        self.client.create_bucket(Bucket=empty_bucket)
        files = list_bucket_files(self.client, empty_bucket)
        assert files == []
    
    def test_list_files_invalid_bucket(self):
        """Test listing files in invalid bucket."""
        files = list_bucket_files(self.client, 'nonexistent-bucket')
        assert files == []


@mock_aws
class TestDirectoryUpload:
    """Test directory upload operations."""
    
    def setup_method(self, method):
        """Set up test bucket and client."""
        self.client = boto3.client('s3', region_name='us-east-1')
        self.bucket_name = 'test-bucket'
        self.client.create_bucket(Bucket=self.bucket_name)
    
    def test_upload_directory_success(self, temp_dir_with_files):
        """Test successful directory upload."""
        result = upload_directory_to_s3(
            self.client,
            temp_dir_with_files,
            self.bucket_name
        )
        
        assert result['success']
        assert result['total_files'] == 6
        assert result['uploaded_files'] == 6
        assert result['skipped_files'] == 0
        assert result['failed_files'] == 0
        assert len(result['errors']) == 0
        
        # Verify all files were uploaded
        files = list_bucket_files(self.client, self.bucket_name)
        assert len(files) == 6
    
    def test_upload_directory_with_prefix(self, temp_dir_with_files):
        """Test directory upload with S3 prefix."""
        result = upload_directory_to_s3(
            self.client,
            temp_dir_with_files,
            self.bucket_name,
            prefix='wedding-photos'
        )
        
        assert result['success']
        
        # Verify files have correct prefix
        files = list_bucket_files(self.client, self.bucket_name)
        assert all(f.startswith('wedding-photos/') for f in files)
    
    def test_upload_directory_skip_existing(self, temp_dir_with_files):
        """Test directory upload skips existing files."""
        # Upload once
        upload_directory_to_s3(self.client, temp_dir_with_files, self.bucket_name)
        
        # Upload again
        result = upload_directory_to_s3(
            self.client,
            temp_dir_with_files,
            self.bucket_name
        )
        
        assert result['success']
        assert result['uploaded_files'] == 0
        assert result['skipped_files'] == 6
    
    def test_upload_directory_dry_run(self, temp_dir_with_files):
        """Test dry run doesn't upload files."""
        result = upload_directory_to_s3(
            self.client,
            temp_dir_with_files,
            self.bucket_name,
            dry_run=True
        )
        
        assert result['success']
        assert result['total_files'] == 6
        
        # Verify no files were uploaded
        files = list_bucket_files(self.client, self.bucket_name)
        assert len(files) == 0
    
    def test_upload_directory_with_progress(self, temp_dir_with_files):
        """Test directory upload with progress callback."""
        progress_calls = []
        
        def progress_callback(filename, current, total):
            progress_calls.append((filename, current, total))
        
        result = upload_directory_to_s3(
            self.client,
            temp_dir_with_files,
            self.bucket_name,
            progress_callback=progress_callback
        )
        
        assert result['success']
        assert len(progress_calls) == 6
        
        # Check progress was reported correctly
        for i, (filename, current, total) in enumerate(progress_calls):
            assert current == i + 1
            assert total == 6
    
    def test_upload_empty_directory(self, tmp_path):
        """Test uploading empty directory."""
        empty_dir = tmp_path / "empty"
        empty_dir.mkdir()
        
        result = upload_directory_to_s3(
            self.client,
            empty_dir,
            self.bucket_name
        )
        
        assert result['success']
        assert result['total_files'] == 0
        assert result['uploaded_files'] == 0


@pytest.fixture
def create_test_image_with_exif():
    """Factory fixture to create test images with custom EXIF data."""
    
    def _create_image(**exif_tags):
        # Create a simple test image
        img = Image.new("RGB", (100, 100), color="red")
        
        # Build EXIF dict from kwargs
        exif_dict = {
            "0th": {},
            "Exif": {},
            "1st": {},
            "GPS": {},
        }
        
        # Add tags based on kwargs
        for tag_name, value in exif_tags.items():
            if tag_name == "DateTimeOriginal":
                exif_dict["Exif"][piexif.ExifIFD.DateTimeOriginal] = (
                    value.encode() if isinstance(value, str) else value
                )
            elif tag_name == "OffsetTimeOriginal":
                exif_dict["Exif"][piexif.ExifIFD.OffsetTimeOriginal] = (
                    value.encode() if isinstance(value, str) else value
                )
            elif tag_name == "Make":
                exif_dict["0th"][piexif.ImageIFD.Make] = (
                    value.encode() if isinstance(value, str) else value
                )
            elif tag_name == "Model":
                exif_dict["0th"][piexif.ImageIFD.Model] = (
                    value.encode() if isinstance(value, str) else value
                )
        
        # Convert EXIF dict to bytes
        exif_bytes = piexif.dump(exif_dict)
        
        # Save image to bytes with EXIF
        img_buffer = io.BytesIO()
        img.save(img_buffer, format='JPEG', exif=exif_bytes)
        return img_buffer.getvalue()
    
    return _create_image


class TestExifModification:
    """Test EXIF modification functionality."""
    
    def test_modify_exif_updates_datetime_original(self, create_test_image_with_exif):
        """Test that modify_exif_in_memory updates DateTimeOriginal."""
        # Create test image with original timestamp
        original_image_bytes = create_test_image_with_exif(
            DateTimeOriginal="2023:12:25 10:30:45"
        )
        
        # New corrected timestamp
        corrected_timestamp = datetime(2023, 12, 25, 8, 30, 45)  # 2 hours earlier
        target_timezone_offset_hours = -5  # EST timezone
        
        # Modify EXIF
        modified_image_bytes = modify_exif_in_memory(
            original_image_bytes, 
            corrected_timestamp, 
            target_timezone_offset_hours
        )
        
        # Verify modification
        exif_dict = piexif.load(modified_image_bytes)
        modified_datetime = exif_dict["Exif"][piexif.ExifIFD.DateTimeOriginal].decode()
        
        assert modified_datetime == "2023:12:25 08:30:45"
    
    def test_modify_exif_sets_timezone_offset(self, create_test_image_with_exif):
        """Test that modify_exif_in_memory sets OffsetTimeOriginal correctly."""
        original_image_bytes = create_test_image_with_exif(
            DateTimeOriginal="2023:12:25 10:30:45"
        )
        
        corrected_timestamp = datetime(2023, 12, 25, 10, 30, 45)
        target_timezone_offset_hours = -5  # EST timezone
        
        modified_image_bytes = modify_exif_in_memory(
            original_image_bytes, 
            corrected_timestamp, 
            target_timezone_offset_hours
        )
        
        # Verify timezone offset was set
        exif_dict = piexif.load(modified_image_bytes)
        offset_time = exif_dict["Exif"][piexif.ExifIFD.OffsetTimeOriginal].decode()
        
        assert offset_time == "-05:00"
    
    def test_modify_exif_positive_timezone_offset(self, create_test_image_with_exif):
        """Test positive timezone offset formatting."""
        original_image_bytes = create_test_image_with_exif(
            DateTimeOriginal="2023:12:25 10:30:45"
        )
        
        corrected_timestamp = datetime(2023, 12, 25, 10, 30, 45)
        target_timezone_offset_hours = 2  # CET timezone
        
        modified_image_bytes = modify_exif_in_memory(
            original_image_bytes, 
            corrected_timestamp, 
            target_timezone_offset_hours
        )
        
        exif_dict = piexif.load(modified_image_bytes)
        offset_time = exif_dict["Exif"][piexif.ExifIFD.OffsetTimeOriginal].decode()
        
        assert offset_time == "+02:00"
    
    def test_modify_exif_preserves_original_timezone_when_offset_13(self, create_test_image_with_exif):
        """Test that offset 13 preserves original timezone."""
        original_image_bytes = create_test_image_with_exif(
            DateTimeOriginal="2023:12:25 10:30:45",
            OffsetTimeOriginal="+01:00"  # Original timezone
        )
        
        corrected_timestamp = datetime(2023, 12, 25, 8, 30, 45)
        target_timezone_offset_hours = 13  # Special "preserve original" value
        
        modified_image_bytes = modify_exif_in_memory(
            original_image_bytes, 
            corrected_timestamp, 
            target_timezone_offset_hours
        )
        
        # Verify timestamp was updated but timezone preserved
        exif_dict = piexif.load(modified_image_bytes)
        modified_datetime = exif_dict["Exif"][piexif.ExifIFD.DateTimeOriginal].decode()
        offset_time = exif_dict["Exif"][piexif.ExifIFD.OffsetTimeOriginal].decode()
        
        assert modified_datetime == "2023:12:25 08:30:45"
        assert offset_time == "+01:00"  # Original timezone preserved
    
    def test_modify_exif_handles_missing_original_timezone_with_offset_13(self, create_test_image_with_exif):
        """Test that offset 13 doesn't add timezone if none exists."""
        original_image_bytes = create_test_image_with_exif(
            DateTimeOriginal="2023:12:25 10:30:45"
            # No OffsetTimeOriginal tag
        )
        
        corrected_timestamp = datetime(2023, 12, 25, 8, 30, 45)
        target_timezone_offset_hours = 13  # Special "preserve original" value
        
        modified_image_bytes = modify_exif_in_memory(
            original_image_bytes, 
            corrected_timestamp, 
            target_timezone_offset_hours
        )
        
        # Verify timestamp was updated but no timezone was added
        exif_dict = piexif.load(modified_image_bytes)
        modified_datetime = exif_dict["Exif"][piexif.ExifIFD.DateTimeOriginal].decode()
        
        assert modified_datetime == "2023:12:25 08:30:45"
        # Should not have OffsetTimeOriginal tag
        assert piexif.ExifIFD.OffsetTimeOriginal not in exif_dict["Exif"]
    
    def test_modify_exif_preserves_other_exif_data(self, create_test_image_with_exif):
        """Test that modify_exif_in_memory preserves other EXIF data."""
        original_image_bytes = create_test_image_with_exif(
            DateTimeOriginal="2023:12:25 10:30:45",
            Make="Canon",
            Model="EOS R5"
        )
        
        corrected_timestamp = datetime(2023, 12, 25, 8, 30, 45)
        target_timezone_offset_hours = -5
        
        modified_image_bytes = modify_exif_in_memory(
            original_image_bytes, 
            corrected_timestamp, 
            target_timezone_offset_hours
        )
        
        # Verify other EXIF data was preserved
        exif_dict = piexif.load(modified_image_bytes)
        make = exif_dict["0th"][piexif.ImageIFD.Make].decode()
        model = exif_dict["0th"][piexif.ImageIFD.Model].decode()
        
        assert make == "Canon"
        assert model == "EOS R5"
    
    def test_modify_exif_preserves_image_quality(self, create_test_image_with_exif):
        """Test that image data is preserved during EXIF modification."""
        original_image_bytes = create_test_image_with_exif(
            DateTimeOriginal="2023:12:25 10:30:45"
        )
        
        # Calculate hash of original image data (without EXIF)
        original_img = Image.open(io.BytesIO(original_image_bytes))
        original_img_buffer = io.BytesIO()
        original_img.save(original_img_buffer, format='JPEG')
        original_hash = hashlib.sha256(original_img_buffer.getvalue()).hexdigest()
        
        corrected_timestamp = datetime(2023, 12, 25, 8, 30, 45)
        target_timezone_offset_hours = -5
        
        modified_image_bytes = modify_exif_in_memory(
            original_image_bytes, 
            corrected_timestamp, 
            target_timezone_offset_hours
        )
        
        # Calculate hash of modified image data (without EXIF)
        modified_img = Image.open(io.BytesIO(modified_image_bytes))
        modified_img_buffer = io.BytesIO()
        modified_img.save(modified_img_buffer, format='JPEG')
        modified_hash = hashlib.sha256(modified_img_buffer.getvalue()).hexdigest()
        
        # Image data should be identical (only EXIF changed)
        assert original_hash == modified_hash
    
    def test_modify_exif_hash_changes_with_different_settings(self, create_test_image_with_exif):
        """Test that deployment hash changes when timezone settings change."""
        original_image_bytes = create_test_image_with_exif(
            DateTimeOriginal="2023:12:25 10:30:45"
        )
        
        corrected_timestamp = datetime(2023, 12, 25, 8, 30, 45)
        
        # Modify with different timezone settings
        modified_bytes_est = modify_exif_in_memory(
            original_image_bytes, corrected_timestamp, -5
        )
        modified_bytes_cet = modify_exif_in_memory(
            original_image_bytes, corrected_timestamp, 2
        )
        modified_bytes_preserve = modify_exif_in_memory(
            original_image_bytes, corrected_timestamp, 13
        )
        
        # Calculate hashes
        hash_est = hashlib.sha256(modified_bytes_est).hexdigest()
        hash_cet = hashlib.sha256(modified_bytes_cet).hexdigest()
        hash_preserve = hashlib.sha256(modified_bytes_preserve).hexdigest()
        
        # All hashes should be different
        assert hash_est != hash_cet
        assert hash_est != hash_preserve
        assert hash_cet != hash_preserve