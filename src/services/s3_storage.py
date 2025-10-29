import boto3
import hashlib
import io
from datetime import datetime
from pathlib import Path
from typing import Optional, Callable, Dict, Any
from botocore.exceptions import ClientError
from PIL import Image
import piexif


def get_s3_client(endpoint: str, access_key: str, secret_key: str, region: str):
    """Create boto3 S3 client for any S3-compatible service.
    
    Args:
        endpoint: S3 endpoint URL (e.g., 'eu-central-1.s3.hetznerobjects.com')
        access_key: S3 access key ID
        secret_key: S3 secret access key
        region: S3 region for the provider
        
    Returns:
        boto3 S3 client configured for the endpoint
    """
    return boto3.client(
        's3',
        endpoint_url=f'https://{endpoint}',
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name=region
    )


def file_exists_in_s3(client, bucket: str, key: str) -> bool:
    """Check if file already exists in S3 bucket.
    
    Args:
        client: boto3 S3 client
        bucket: S3 bucket name
        key: S3 object key
        
    Returns:
        True if file exists, False otherwise
    """
    try:
        client.head_object(Bucket=bucket, Key=key)
        return True
    except ClientError as e:
        if e.response['Error']['Code'] == '404':
            return False
        raise


def calculate_file_checksum(file_path: Path) -> str:
    """Calculate SHA256 checksum of a file.
    
    Args:
        file_path: Path to file
        
    Returns:
        Hex-encoded SHA256 checksum
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def upload_file_to_s3(
    client,
    local_path: Path,
    bucket: str,
    key: str,
    progress_callback: Optional[Callable[[int], None]] = None
) -> Dict[str, Any]:
    """Upload single file to S3 with progress tracking.
    
    Args:
        client: boto3 S3 client
        local_path: Path to local file
        bucket: S3 bucket name
        key: S3 object key (path in bucket)
        progress_callback: Optional callback for progress updates
        
    Returns:
        Dict with upload results:
        {
            'success': bool,
            'key': str,
            'size': int,
            'checksum': str,
            'error': str (if failed)
        }
    """
    result = {
        'success': False,
        'key': key,
        'size': local_path.stat().st_size,
        'checksum': None,
        'error': None
    }
    
    try:
        # Calculate checksum before upload
        result['checksum'] = calculate_file_checksum(local_path)
        
        # Check if file already exists
        if file_exists_in_s3(client, bucket, key):
            result['success'] = True
            result['error'] = 'File already exists (skipped)'
            return result
        
        # Upload file
        if progress_callback:
            client.upload_file(
                str(local_path),
                bucket,
                key,
                Callback=progress_callback
            )
        else:
            client.upload_file(
                str(local_path),
                bucket,
                key
            )
        
        result['success'] = True
        
    except Exception as e:
        result['error'] = f"Upload error: {str(e)}"
    
    return result


def list_bucket_files(client, bucket: str, prefix: str = '') -> list:
    """List all files in bucket with given prefix.
    
    Args:
        client: boto3 S3 client
        bucket: S3 bucket name
        prefix: S3 key prefix to filter by
        
    Returns:
        List of S3 object keys
    """
    try:
        response = client.list_objects_v2(Bucket=bucket, Prefix=prefix)
        return [obj['Key'] for obj in response.get('Contents', [])]
    except ClientError:
        return []


def upload_directory_to_s3(
    client,
    local_dir: Path,
    bucket: str,
    prefix: str = '',
    dry_run: bool = False,
    progress_callback: Optional[Callable[[str, int, int], None]] = None
) -> Dict[str, Any]:
    """Upload entire directory to S3 preserving structure.
    
    Args:
        client: boto3 S3 client
        local_dir: Path to local directory
        bucket: S3 bucket name
        prefix: S3 key prefix (subdirectory in bucket)
        dry_run: If True, don't actually upload, just simulate
        progress_callback: Optional callback(filename, current, total)
        
    Returns:
        Dict with upload results:
        {
            'success': bool,
            'total_files': int,
            'uploaded_files': int,
            'skipped_files': int,
            'failed_files': int,
            'total_size': int,
            'errors': List[str]
        }
    """
    # Find all files to upload
    all_files = []
    for file_path in local_dir.rglob('*'):
        if file_path.is_file():
            all_files.append(file_path)
    
    result = {
        'success': True,
        'total_files': len(all_files),
        'uploaded_files': 0,
        'skipped_files': 0,
        'failed_files': 0,
        'total_size': sum(f.stat().st_size for f in all_files),
        'errors': []
    }
    
    if dry_run:
        result['success'] = True
        return result
    
    # Upload each file
    for i, file_path in enumerate(all_files, 1):
        # Calculate S3 key (preserve directory structure)
        relative_path = file_path.relative_to(local_dir)
        s3_key = f"{prefix.rstrip('/')}/{relative_path}".lstrip('/')
        
        if progress_callback:
            progress_callback(file_path.name, i, len(all_files))
        
        upload_result = upload_file_to_s3(client, file_path, bucket, s3_key)
        
        if upload_result['success']:
            if upload_result.get('error') and 'already exists' in upload_result['error']:
                result['skipped_files'] += 1
            else:
                result['uploaded_files'] += 1
        else:
            result['failed_files'] += 1
            result['errors'].append(f"{file_path.name}: {upload_result['error']}")
    
    result['success'] = result['failed_files'] == 0
    return result


def modify_exif_in_memory(
    image_bytes: bytes, 
    corrected_timestamp: datetime, 
    target_timezone_offset_hours: int
) -> bytes:
    """Modify EXIF data in memory with corrected timestamp and timezone.
    
    Args:
        image_bytes: Original image data as bytes
        corrected_timestamp: Corrected timestamp to set in DateTimeOriginal
        target_timezone_offset_hours: Target timezone offset in hours
                                    (13 = preserve original timezone)
    
    Returns:
        Modified image bytes with updated EXIF data
        
    Raises:
        Exception: If image cannot be processed or EXIF modification fails
    """
    # Load the image and EXIF data
    img = Image.open(io.BytesIO(image_bytes))
    
    try:
        exif_dict = piexif.load(image_bytes)
    except piexif.InvalidImageDataError:
        # Create empty EXIF dict if none exists
        exif_dict = {
            "0th": {},
            "Exif": {},
            "1st": {},
            "GPS": {},
        }
    
    # Update DateTimeOriginal with corrected timestamp
    datetime_str = corrected_timestamp.strftime("%Y:%m:%d %H:%M:%S")
    exif_dict["Exif"][piexif.ExifIFD.DateTimeOriginal] = datetime_str.encode()
    
    # Handle timezone offset
    if target_timezone_offset_hours != 13:
        # Format timezone offset as ±HH:MM per EXIF 2.31 standard
        sign = "+" if target_timezone_offset_hours >= 0 else "-"
        hours = abs(target_timezone_offset_hours)
        timezone_str = f"{sign}{hours:02d}:00"
        exif_dict["Exif"][piexif.ExifIFD.OffsetTimeOriginal] = timezone_str.encode()
    # If target_timezone_offset_hours == 13, preserve original timezone (don't modify)
    
    # Convert EXIF dict back to bytes
    exif_bytes = piexif.dump(exif_dict)
    
    # Save image with modified EXIF to bytes
    output_buffer = io.BytesIO()
    img.save(output_buffer, format='JPEG', exif=exif_bytes)
    
    return output_buffer.getvalue()


def get_bucket_cors(client, bucket: str) -> Dict[str, Any]:
    """Get current CORS configuration for an S3 bucket.
    
    Args:
        client: boto3 S3 client
        bucket: S3 bucket name
        
    Returns:
        Dict with:
        - success: bool indicating if operation succeeded
        - cors_rules: list of CORS rules if successful
        - error: error message if failed
    """
    try:
        response = client.get_bucket_cors(Bucket=bucket)
        return {
            'success': True,
            'cors_rules': response.get('CORSRules', [])
        }
    except ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == 'NoSuchCORSConfiguration':
            return {
                'success': True,
                'cors_rules': []
            }
        else:
            return {
                'success': False,
                'error': f"Failed to get CORS configuration: {str(e)}"
            }


def configure_bucket_cors(client, bucket: str, cors_rules: list) -> Dict[str, Any]:
    """Configure CORS rules for an S3 bucket.
    
    Args:
        client: boto3 S3 client
        bucket: S3 bucket name
        cors_rules: List of CORS rule dictionaries
        
    Returns:
        Dict with:
        - success: bool indicating if operation succeeded
        - error: error message if failed
    """
    try:
        cors_configuration = {'CORSRules': cors_rules}
        client.put_bucket_cors(
            Bucket=bucket,
            CORSConfiguration=cors_configuration
        )
        return {'success': True}
    except ClientError as e:
        return {
            'success': False,
            'error': f"Failed to configure CORS: {str(e)}"
        }


def get_default_gallery_cors_rules() -> list:
    """Get default CORS rules for gallery web access.
    
    Returns:
        List of CORS rule dictionaries suitable for gallery deployment
    """
    return [
        {
            'AllowedHeaders': ['*'],
            'AllowedMethods': ['GET', 'HEAD'],
            'AllowedOrigins': ['*'],
            'ExposeHeaders': ['ETag'],
            'MaxAgeSeconds': 3600
        }
    ]


def cors_rules_match(current_rules: list, expected_rules: list) -> bool:
    """Check if current CORS rules match expected rules.
    
    Args:
        current_rules: Current CORS rules from bucket
        expected_rules: Expected CORS rules
        
    Returns:
        True if rules match, False otherwise
    """
    if len(current_rules) != len(expected_rules):
        return False
    
    for current, expected in zip(current_rules, expected_rules):
        # Check required fields match
        for field in ['AllowedMethods', 'AllowedOrigins']:
            if set(current.get(field, [])) != set(expected.get(field, [])):
                return False
        
        # Check MaxAgeSeconds if specified
        if expected.get('MaxAgeSeconds') and current.get('MaxAgeSeconds') != expected.get('MaxAgeSeconds'):
            return False
    
    return True


def examine_bucket_cors(client, bucket: str) -> Dict[str, Any]:
    """Examine bucket CORS configuration and compare with expected rules.
    
    Args:
        client: boto3 S3 client
        bucket: S3 bucket name
        
    Returns:
        Dict with:
        - success: bool indicating if examination succeeded
        - configured: bool indicating if CORS is properly configured
        - current_rules: current CORS rules
        - expected_rules: expected CORS rules for gallery
        - needs_update: bool indicating if CORS rules need updating
        - error: error message if failed
    """
    # Get current CORS rules
    cors_result = get_bucket_cors(client, bucket)
    if not cors_result['success']:
        return {
            'success': False,
            'error': cors_result['error']
        }
    
    current_rules = cors_result['cors_rules']
    expected_rules = get_default_gallery_cors_rules()
    
    # Check if rules match
    configured = len(current_rules) > 0
    needs_update = not cors_rules_match(current_rules, expected_rules)
    
    return {
        'success': True,
        'configured': configured,
        'current_rules': current_rules,
        'expected_rules': expected_rules,
        'needs_update': needs_update
    }