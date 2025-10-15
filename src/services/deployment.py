"""Deployment service functions for galleria."""
from pathlib import Path
from typing import Optional, Callable, Dict, Any

from .s3_storage import upload_directory_to_s3


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