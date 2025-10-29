"""Deploy command for galleria photo gallery."""
import click
import sys
import json
from pathlib import Path

from src.command.upload_photos import validate_s3_config
from src.services.s3_storage import get_s3_client, examine_bucket_cors, configure_bucket_cors, get_default_gallery_cors_rules
from src.services.deployment import deploy_directory_to_s3, deploy_gallery_metadata
from src.models.photo import GalleryMetadata


def load_local_gallery_metadata(prod_dir: Path) -> GalleryMetadata:
    """Load gallery metadata from local file system.
    
    Args:
        prod_dir: Path to production directory containing gallery-metadata.json
        
    Returns:
        GalleryMetadata object
        
    Raises:
        FileNotFoundError: If gallery-metadata.json doesn't exist
        json.JSONDecodeError: If the JSON is invalid
    """
    metadata_file = prod_dir / "gallery-metadata.json"
    
    if not metadata_file.exists():
        raise FileNotFoundError(f"Gallery metadata not found: {metadata_file}")
    
    with open(metadata_file, 'r') as f:
        data = json.load(f)
    
    return GalleryMetadata.from_dict(data)


@click.command()
@click.option('--source', '-s', 
              type=click.Path(exists=True, file_okay=False, path_type=Path),
              help='Override OUTPUT_DIR for source directory')
@click.option('--dry-run', is_flag=True,
              help='Show deployment plan without executing')
@click.option('--force', is_flag=True,
              help='Upload all photos ignoring hash comparison')
@click.option('--progress', is_flag=True,
              help='Show detailed progress during upload')
@click.option('--invalidate-cdn', is_flag=True,
              help='Trigger CDN cache purge')
@click.option('--photos-only', 'mode_photos', is_flag=True,
              help='Upload only photos/metadata (skip static site)')
@click.option('--site-only', 'mode_site', is_flag=True,
              help='Upload only static site files (skip photos)')
@click.option('--setup-cors', is_flag=True,
              help='Configure bucket CORS rules for web access')
def deploy(source, dry_run, force, progress, invalidate_cdn, mode_photos, mode_site, setup_cors):
    """Deploy complete gallery (photos + static site) to production hosting."""
    
    # Validate mutually exclusive options
    if mode_photos and mode_site:
        raise click.ClickException("Options --photos-only and --site-only are mutually exclusive and cannot be used together.")
    
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
    
    # Determine source directories
    static_site_dir = source or settings.OUTPUT_DIR
    photos_dir = settings.BASE_DIR / 'prod' / 'pics'
    
    # Create S3 client
    try:
        client = get_s3_client(
            endpoint=settings.S3_PUBLIC_ENDPOINT,
            access_key=settings.S3_PUBLIC_ACCESS_KEY,
            secret_key=settings.S3_PUBLIC_SECRET_KEY,
            region=settings.S3_PUBLIC_REGION
        )
    except Exception as e:
        click.echo(f"Error creating S3 client: {str(e)}", err=True)
        sys.exit(1)
    
    # Examine bucket CORS configuration
    click.echo(f"{'[DRY RUN] ' if dry_run else ''}Deploying gallery to S3...")
    click.echo(f"Bucket: {settings.S3_PUBLIC_BUCKET}")
    
    cors_examination = examine_bucket_cors(client, settings.S3_PUBLIC_BUCKET)
    cors_configured_properly = False
    
    if cors_examination['success']:
        if cors_examination['configured'] and not cors_examination['needs_update']:
            click.echo("CORS Status: Configured correctly for web access")
            cors_configured_properly = True
        elif cors_examination['configured'] and cors_examination['needs_update']:
            click.echo("CORS Status: Configured but rules need updating")
            if setup_cors:
                click.echo("Updating CORS rules...")
                cors_result = configure_bucket_cors(client, settings.S3_PUBLIC_BUCKET, get_default_gallery_cors_rules())
                if cors_result['success']:
                    click.echo("CORS Status: Updated successfully")
                    cors_configured_properly = True
                else:
                    click.echo(f"CORS Error: {cors_result['error']}", err=True)
                    sys.exit(1)
            else:
                click.echo("Use --setup-cors to update CORS rules")
                click.echo("Deployment aborted: CORS configuration required for web access", err=True)
                sys.exit(1)
        else:
            click.echo("CORS Status: Not configured for web access")
            if setup_cors:
                click.echo("Configuring CORS rules...")
                cors_result = configure_bucket_cors(client, settings.S3_PUBLIC_BUCKET, get_default_gallery_cors_rules())
                if cors_result['success']:
                    click.echo("CORS Status: Configured successfully")
                    cors_configured_properly = True
                else:
                    click.echo(f"CORS Error: {cors_result['error']}", err=True)
                    sys.exit(1)
            else:
                click.echo("Use --setup-cors to configure CORS for web access")
                click.echo("Deployment aborted: CORS configuration required for web access", err=True)
                sys.exit(1)
    else:
        click.echo(f"CORS Status: Could not examine CORS: {cors_examination['error']}", err=True)
        click.echo("Deployment aborted: Unable to verify bucket configuration", err=True)
        sys.exit(1)
    
    # Check if we have gallery metadata for enhanced deployment
    metadata_file = photos_dir / "gallery-metadata.json"
    use_metadata_deployment = metadata_file.exists() and not mode_site
    
    if use_metadata_deployment:
        # Enhanced metadata-driven deployment
        click.echo(f"Using metadata-driven deployment...")
        
        try:
            local_metadata = load_local_gallery_metadata(photos_dir)
            
            # Use deploy_gallery_metadata for photos
            deployment_result = deploy_gallery_metadata(
                client=client,
                bucket=settings.S3_PUBLIC_BUCKET,
                local_metadata=local_metadata,
                prod_dir=photos_dir,
                dry_run=dry_run
            )
            
            if dry_run and deployment_result.get('success'):
                # Show deployment plan and exit (dry-run doesn't execute)
                plan = deployment_result.get('plan', {})
                click.echo(f"\nDeployment Plan:")
                click.echo(f"  Photos to upload: {len(plan.get('upload', []))}")
                click.echo(f"  Photos to delete: {len(plan.get('delete', []))}")
                click.echo(f"  Photos unchanged: {len(plan.get('unchanged', []))}")
                click.echo("\nDry run completed - no files were uploaded")
                return 0
            
            if not deployment_result.get('success'):
                click.echo(f"Photo deployment failed: {deployment_result.get('error', 'Unknown error')}", err=True)
                sys.exit(1)
            
            total_uploaded = deployment_result.get('photos_uploaded', 0)
            click.echo(f"Photos: {total_uploaded} uploaded")
            
        except (FileNotFoundError, json.JSONDecodeError) as e:
            click.echo(f"Error loading gallery metadata: {e}", err=True)
            sys.exit(1)
    
    else:
        # Fallback to directory-based deployment
        click.echo(f"Using directory-based deployment...")
        
        total_uploaded = 0
        total_files = 0
        deployment_errors = []
        
        # Deploy photos (unless site-only mode)
        if not mode_site:
            click.echo(f"\nDeploying photos from: {photos_dir}")
            photos_result = deploy_directory_to_s3(
                client=client,
                source_dir=photos_dir,
                bucket=settings.S3_PUBLIC_BUCKET,
                prefix="photos",
                dry_run=dry_run
            )
            
            if photos_result['success']:
                click.echo(f"Photos: {photos_result['uploaded_files']} uploaded, {photos_result['skipped_files']} skipped")
            else:
                click.echo(f"Photos deployment failed: {photos_result.get('error', 'Unknown error')}", err=True)
                deployment_errors.extend(photos_result.get('errors', []))
            
            total_uploaded += photos_result['uploaded_files']
            total_files += photos_result['total_files']
    
    # Deploy static site (unless photos-only mode)
    if not mode_photos:
        click.echo(f"\nDeploying static site from: {static_site_dir}")
        site_result = deploy_directory_to_s3(
            client=client,
            source_dir=static_site_dir,
            bucket=settings.S3_PUBLIC_BUCKET,
            prefix="",
            dry_run=dry_run
        )
        
        if site_result['success']:
            click.echo(f"Static site: {site_result['uploaded_files']} uploaded, {site_result['skipped_files']} skipped")
        else:
            click.echo(f"Static site deployment failed: {site_result.get('error', 'Unknown error')}", err=True)
            if not use_metadata_deployment:
                deployment_errors.extend(site_result.get('errors', []))
        
        if not use_metadata_deployment:
            total_uploaded += site_result['uploaded_files']
            total_files += site_result['total_files']
    
    # TODO: Implement CDN invalidation when --invalidate-cdn is specified
    if invalidate_cdn:
        click.echo("\nCDN invalidation requested (not yet implemented)")
    
    # Summary
    if not use_metadata_deployment:
        click.echo(f"\nDeployment Summary:")
        click.echo(f"Total files processed: {total_files}")
        click.echo(f"Files uploaded: {total_uploaded}")
        
        if deployment_errors:
            click.echo(f"\nErrors encountered:", err=True)
            for error in deployment_errors:
                click.echo(f"  - {error}", err=True)
            sys.exit(1)
    
    click.echo("\nDeployment completed successfully!")
    return 0