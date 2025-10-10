import boto3
import hashlib
from pathlib import Path
from typing import Optional, Callable, Dict, Any
from botocore.exceptions import ClientError


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
        extra_args = {}
        if progress_callback:
            extra_args['Callback'] = progress_callback
            
        client.upload_file(
            str(local_path),
            bucket,
            key,
            ExtraArgs=extra_args
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