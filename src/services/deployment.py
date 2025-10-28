"""Deployment service functions for galleria."""
import json
from pathlib import Path
from typing import Optional, Callable, Dict, Any, List
from botocore.exceptions import ClientError

from .s3_storage import upload_directory_to_s3
from ..models.photo import GalleryMetadata, PhotoMetadata


def deploy_directory_to_s3(
    client,
    source_dir: Path,
    bucket: str,
    prefix: str = "",
    dry_run: bool = False,
    progress_callback: Optional[Callable[[str, int, int], None]] = None
) -> Dict[str, Any]:
    """Deploy a directory to S3 with comprehensive error handling.
    
    This is a wrapper around upload_directory_to_s3 that provides
    additional validation and standardized error handling for deployment operations.
    
    Args:
        client: boto3 S3 client
        source_dir: Path to local directory to deploy
        bucket: S3 bucket name
        prefix: S3 key prefix (subdirectory in bucket)
        dry_run: If True, don't actually upload, just simulate
        progress_callback: Optional callback(filename, current, total)
        
    Returns:
        Dict with deployment results:
        {
            'success': bool,
            'total_files': int,
            'uploaded_files': int,
            'skipped_files': int,
            'failed_files': int,
            'total_size': int,
            'errors': List[str],
            'error': str (if failed validation)
        }
    """
    # Validate source directory exists
    if not source_dir.exists():
        return {
            'success': False,
            'error': f"Source directory does not exist: {source_dir}",
            'total_files': 0,
            'uploaded_files': 0,
            'skipped_files': 0,
            'failed_files': 0,
            'total_size': 0,
            'errors': []
        }
    
    # Delegate to existing upload function
    try:
        result = upload_directory_to_s3(
            client=client,
            local_dir=source_dir,
            bucket=bucket,
            prefix=prefix,
            dry_run=dry_run,
            progress_callback=progress_callback
        )
        return result
        
    except Exception as e:
        return {
            'success': False,
            'error': f"Deployment failed: {str(e)}",
            'total_files': 0,
            'uploaded_files': 0,
            'skipped_files': 0,
            'failed_files': 0,
            'total_size': 0,
            'errors': [str(e)]
        }


def download_remote_metadata(client, bucket: str, key: str) -> Optional[GalleryMetadata]:
    """Download and parse remote metadata from S3.
    
    Args:
        client: boto3 S3 client
        bucket: S3 bucket name
        key: S3 object key for metadata file
        
    Returns:
        GalleryMetadata object if successful, None if file doesn't exist or invalid
    """
    try:
        response = client.get_object(Bucket=bucket, Key=key)
        metadata_json = response['Body'].read().decode('utf-8')
        metadata_dict = json.loads(metadata_json)
        return GalleryMetadata.from_dict(metadata_dict)
        
    except ClientError as e:
        if e.response['Error']['Code'] == 'NoSuchKey':
            return None
        raise
    except (json.JSONDecodeError, KeyError, TypeError):
        return None


def generate_deployment_plan(
    local_metadata: GalleryMetadata, 
    remote_metadata: Optional[GalleryMetadata]
) -> Dict[str, List]:
    """Generate deployment plan by comparing local and remote metadata.
    
    Args:
        local_metadata: Local gallery metadata
        remote_metadata: Remote gallery metadata (None if doesn't exist)
        
    Returns:
        Dict with lists of photos to upload, delete, and unchanged:
        {
            'upload': List[PhotoMetadata],    # Photos to upload
            'delete': List[str],              # Photo IDs to delete
            'unchanged': List[PhotoMetadata]  # Photos that are unchanged
        }
    """
    plan = {
        'upload': [],
        'delete': [],
        'unchanged': []
    }
    
    # Create map of remote photos by ID for quick lookup
    remote_photos = {}
    if remote_metadata:
        remote_photos = {photo.id: photo for photo in remote_metadata.photos}
    
    # Check each local photo
    for local_photo in local_metadata.photos:
        remote_photo = remote_photos.get(local_photo.id)
        
        if not remote_photo:
            # New photo - needs upload
            plan['upload'].append(local_photo)
        elif local_photo.deployment_file_hash != remote_photo.deployment_file_hash:
            # Photo changed - needs upload
            plan['upload'].append(local_photo)
        else:
            # Photo unchanged
            plan['unchanged'].append(local_photo)
    
    # Check for orphaned remote photos
    if remote_metadata:
        local_photo_ids = {photo.id for photo in local_metadata.photos}
        for remote_photo in remote_metadata.photos:
            if remote_photo.id not in local_photo_ids:
                plan['delete'].append(remote_photo.id)
    
    return plan


def verify_s3_state(client, bucket: str, metadata: GalleryMetadata) -> Dict[str, Any]:
    """Verify that S3 state matches the expected metadata.
    
    Args:
        client: boto3 S3 client
        bucket: S3 bucket name
        metadata: Expected gallery metadata
        
    Returns:
        Dict with verification results:
        {
            'consistent': bool,
            'missing_files': List[str],
            'orphaned_files': List[str]
        }
    """
    try:
        # List all files in bucket
        response = client.list_objects_v2(Bucket=bucket)
        remote_files = set()
        if 'Contents' in response:
            remote_files = {obj['Key'] for obj in response['Contents']}
        
        # Expected files based on metadata
        expected_files = set()
        for photo in metadata.photos:
            expected_files.add(photo.files.full)
            expected_files.add(photo.files.web)
            expected_files.add(photo.files.thumb)
        expected_files.add('gallery-metadata.json')
        
        # Find missing and orphaned files
        missing_files = expected_files - remote_files
        orphaned_files = remote_files - expected_files
        
        return {
            'consistent': len(missing_files) == 0 and len(orphaned_files) == 0,
            'missing_files': list(missing_files),
            'orphaned_files': list(orphaned_files)
        }
        
    except ClientError:
        return {
            'consistent': False,
            'missing_files': [],
            'orphaned_files': []
        }


def deploy_gallery_metadata(
    client,
    bucket: str,
    local_metadata: GalleryMetadata,
    prod_dir: Path,
    dry_run: bool = False
) -> Dict[str, Any]:
    """Deploy gallery with metadata-last upload ordering for atomic consistency.
    
    Args:
        client: boto3 S3 client
        bucket: S3 bucket name
        local_metadata: Local gallery metadata to deploy
        prod_dir: Path to production directory containing photos and metadata
        dry_run: If True, show plan without uploading
        
    Returns:
        Dict with deployment results:
        {
            'success': bool,
            'dry_run': bool,
            'photos_uploaded': int,
            'metadata_uploaded': bool,
            'plan': Dict (if dry_run),
            'message': str,
            'error': str (if failed)
        }
    """
    try:
        # Download remote metadata for comparison
        remote_metadata = download_remote_metadata(client, bucket, "gallery-metadata.json")
        
        # Generate deployment plan
        plan = generate_deployment_plan(local_metadata, remote_metadata)
        
        # If dry run, return plan without uploading
        if dry_run:
            return {
                'success': True,
                'dry_run': True,
                'photos_uploaded': 0,
                'metadata_uploaded': False,
                'plan': {
                    'upload_count': len(plan['upload']),
                    'delete_count': len(plan['delete']),
                    'unchanged_count': len(plan['unchanged']),
                    'photos_to_upload': [photo.id for photo in plan['upload']],
                    'photos_to_delete': plan['delete']
                },
                'message': f"Would upload {len(plan['upload'])} photos, delete {len(plan['delete'])} photos"
            }
        
        # If no changes needed, return early
        if len(plan['upload']) == 0 and len(plan['delete']) == 0:
            return {
                'success': True,
                'dry_run': False,
                'photos_uploaded': 0,
                'metadata_uploaded': False,
                'message': "No changes detected - deployment skipped"
            }
        
        # Upload photos first (before metadata for atomic consistency)
        photos_uploaded = 0
        for photo in plan['upload']:
            # Upload all variants of this photo
            for file_type, file_path in [
                ('full', photo.files.full),
                ('web', photo.files.web),
                ('thumb', photo.files.thumb)
            ]:
                local_file_path = prod_dir / file_path
                if local_file_path.exists():
                    client.upload_file(
                        str(local_file_path),
                        bucket,
                        file_path
                    )
                    photos_uploaded += 1
        
        # Upload metadata last (atomic commit)
        metadata_file = prod_dir / "gallery-metadata.json"
        if metadata_file.exists():
            client.upload_file(
                str(metadata_file),
                bucket,
                "gallery-metadata.json"
            )
            metadata_uploaded = True
        else:
            # Generate metadata file if it doesn't exist
            metadata_content = json.dumps(local_metadata.to_dict(), indent=2)
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as temp_file:
                temp_file.write(metadata_content)
                temp_file.flush()
                client.upload_file(
                    temp_file.name,
                    bucket,
                    "gallery-metadata.json"
                )
                metadata_uploaded = True
            # Clean up temp file
            Path(temp_file.name).unlink()
        
        return {
            'success': True,
            'dry_run': False,
            'photos_uploaded': photos_uploaded,
            'metadata_uploaded': metadata_uploaded,
            'message': f"Successfully deployed {photos_uploaded} photo files and metadata"
        }
        
    except Exception as e:
        return {
            'success': False,
            'dry_run': dry_run,
            'photos_uploaded': 0,
            'metadata_uploaded': False,
            'error': f"Deployment failed: {str(e)}"
        }