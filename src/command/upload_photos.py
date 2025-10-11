"""
Upload processed photos to S3-compatible public gallery bucket.

This command uploads processed photos (full, web, thumbnail) to the configured
public S3 bucket for serving via CDN.
"""
import click
from pathlib import Path
from typing import Optional
import sys

from src.services.s3_storage import (
    get_s3_client,
    upload_directory_to_s3,
    list_bucket_files
)


def validate_s3_config(settings) -> tuple[bool, str]:
    """Validate that all required S3 settings are configured.
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    required_settings = [
        'S3_PUBLIC_ENDPOINT',
        'S3_PUBLIC_ACCESS_KEY',
        'S3_PUBLIC_SECRET_KEY',
        'S3_PUBLIC_BUCKET',
        'S3_PUBLIC_REGION'
    ]
    
    missing = []
    for setting in required_settings:
        if not getattr(settings, setting, None):
            missing.append(setting)
    
    if missing:
        return False, f"Missing required S3 settings: {', '.join(missing)}"
    
    return True, ""


def progress_callback(filename: str, current: int, total: int):
    """Display progress during upload."""
    percentage = (current / total) * 100
    click.echo(f"\r[{current}/{total}] {percentage:.1f}% - Uploading {filename}", nl=False)
    if current == total:
        click.echo()  # New line after completion


@click.command()
@click.option(
    '--source', '-s',
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    help='Directory containing processed photos to upload (defaults to PROCESSED_DIR)'
)
@click.option(
    '--dry-run',
    is_flag=True,
    help='Show what would be uploaded without actually uploading'
)
@click.option(
    '--progress',
    is_flag=True,
    help='Show upload progress'
)
@click.option(
    '--prefix',
    default='',
    help='S3 key prefix (subdirectory in bucket)'
)
def upload_photos(
    source: Optional[Path],
    dry_run: bool,
    progress: bool,
    prefix: str
):
    """Upload processed photos to public S3 gallery bucket."""
    # Import settings after click processes arguments
    import settings
    
    # Validate S3 configuration
    is_valid, error_msg = validate_s3_config(settings)
    if not is_valid:
        click.echo(f"Error: {error_msg}", err=True)
        click.echo("\nPlease configure S3 settings in settings.local.py or environment variables:", err=True)
        click.echo("  - GALLERIA_S3_PUBLIC_ENDPOINT", err=True)
        click.echo("  - GALLERIA_S3_PUBLIC_ACCESS_KEY", err=True)
        click.echo("  - GALLERIA_S3_PUBLIC_SECRET_KEY", err=True)
        click.echo("  - GALLERIA_S3_PUBLIC_BUCKET", err=True)
        click.echo("  - GALLERIA_S3_PUBLIC_REGION", err=True)
        sys.exit(1)
    
    # Use provided source or default from settings
    upload_dir = source or settings.PROCESSED_DIR
    
    if not upload_dir.exists():
        click.echo(f"Error: Source directory does not exist: {upload_dir}", err=True)
        sys.exit(1)
    
    # Count files to upload
    file_count = sum(1 for _ in upload_dir.rglob('*') if _.is_file())
    if file_count == 0:
        click.echo(f"No files found in {upload_dir}")
        return
    
    click.echo(f"{'[DRY RUN] ' if dry_run else ''}Uploading photos to S3...")
    click.echo(f"Source: {upload_dir}")
    click.echo(f"Bucket: {settings.S3_PUBLIC_BUCKET}")
    click.echo(f"Prefix: {prefix or '(root)'}")
    click.echo(f"Files: {file_count}")
    
    if dry_run:
        click.echo("\nDry run - no files will be uploaded")
    
    try:
        # Create S3 client
        client = get_s3_client(
            endpoint=settings.S3_PUBLIC_ENDPOINT,
            access_key=settings.S3_PUBLIC_ACCESS_KEY,
            secret_key=settings.S3_PUBLIC_SECRET_KEY,
            region=settings.S3_PUBLIC_REGION
        )
        
        # List existing files in bucket
        if not dry_run:
            existing_files = list_bucket_files(client, settings.S3_PUBLIC_BUCKET, prefix)
            click.echo(f"Existing files in bucket: {len(existing_files)}")
        
        # Upload directory
        callback = progress_callback if progress and not dry_run else None
        
        result = upload_directory_to_s3(
            client=client,
            local_dir=upload_dir,
            bucket=settings.S3_PUBLIC_BUCKET,
            prefix=prefix,
            dry_run=dry_run,
            progress_callback=callback
        )
        
        # Display results
        click.echo("\nUpload Summary:")
        click.echo(f"Total files: {result['total_files']}")
        click.echo(f"Uploaded: {result['uploaded_files']}")
        click.echo(f"Skipped (already exist): {result['skipped_files']}")
        click.echo(f"Failed: {result['failed_files']}")
        click.echo(f"Total size: {result['total_size'] / (1024*1024):.1f} MB")
        
        if result['errors']:
            click.echo("\nErrors encountered:", err=True)
            for error in result['errors']:
                click.echo(f"  - {error}", err=True)
        
        if result['success']:
            click.echo("\nUpload completed successfully!")
        else:
            click.echo("\nUpload completed with errors", err=True)
            sys.exit(1)
            
    except Exception as e:
        click.echo(f"\nError: {str(e)}", err=True)
        sys.exit(1)