"""
Process photos command for Galleria.

Reads full and web-optimized photo collections, generates chronological filenames,
creates symlinks, and generates thumbnails.
"""
import click
from pathlib import Path
from typing import Optional
import sys

from src.services.file_processing import process_dual_photo_collection
from src.services.photo_validation import validate_matching_collections


@click.command()
@click.option(
    '--full-source', '-f',
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    help='Full resolution photo directory (defaults to PIC_SOURCE_PATH_FULL)'
)
@click.option(
    '--web-source', '-w',
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    help='Web-optimized photo directory (defaults to PIC_SOURCE_PATH_WEB)'
)
@click.option(
    '--output', '-o',
    type=click.Path(file_okay=False, dir_okay=True, path_type=Path),
    help='Output directory (defaults to prod/pics)'
)
@click.option(
    '--collection-name', '-c',
    default='wedding',
    help='Name for this photo collection'
)
@click.option(
    '--skip-validation',
    is_flag=True,
    help='Skip validation and process only matching photos'
)
@click.option(
    '--dry-run',
    is_flag=True,
    help='Show what would be processed without actually doing it'
)
def process_photos(
    full_source: Optional[Path],
    web_source: Optional[Path],
    output: Optional[Path],
    collection_name: str,
    skip_validation: bool,
    dry_run: bool
):
    """Process full and web photo collections with chronological filenames."""
    # Import settings after click processes arguments
    import settings
    
    # Use provided paths or defaults from settings
    full_dir = full_source or settings.PIC_SOURCE_PATH_FULL
    web_dir = web_source or settings.PIC_SOURCE_PATH_WEB
    # Default to prod/pics/ instead of PROCESSED_DIR
    output_dir = output or (settings.BASE_DIR / 'prod' / 'pics')
    
    # Validate directories exist
    if not full_dir.exists():
        click.echo(f"Error: Full resolution directory does not exist: {full_dir}", err=True)
        sys.exit(1)
    
    if not web_dir.exists():
        click.echo(f"Error: Web-optimized directory does not exist: {web_dir}", err=True)
        sys.exit(1)
    
    # Show configuration
    click.echo(f"Processing photo collections:")
    click.echo(f"  Full resolution: {full_dir}")
    click.echo(f"  Web optimized:   {web_dir}")
    click.echo(f"  Output:          {output_dir}")
    click.echo(f"  Collection:      {collection_name}")
    
    if dry_run:
        click.echo("\n[DRY RUN MODE - No files will be created]")
    
    # Validate collections match
    click.echo("\nValidating collections...")
    matched, full_only, web_only = validate_matching_collections(full_dir, web_dir)
    
    click.echo(f"  Matched photos: {len(matched)}")
    if full_only:
        click.echo(f"  Only in full:   {len(full_only)}")
        for name in full_only[:5]:
            click.echo(f"    - {name}")
        if len(full_only) > 5:
            click.echo(f"    ... and {len(full_only) - 5} more")
    
    if web_only:
        click.echo(f"  Only in web:    {len(web_only)}")
        for name in web_only[:5]:
            click.echo(f"    - {name}")
        if len(web_only) > 5:
            click.echo(f"    ... and {len(web_only) - 5} more")
    
    # Check if we should proceed
    if not matched:
        click.echo("\nError: No matching photos found between collections!", err=True)
        sys.exit(1)
    
    if (full_only or web_only) and not skip_validation:
        click.echo("\nError: Collections don't match perfectly.", err=True)
        click.echo("Use --skip-validation to process only matching photos.", err=True)
        sys.exit(1)
    
    if dry_run:
        click.echo(f"\nWould process {len(matched)} matching photos.")
        click.echo("Output structure:")
        click.echo(f"  {output_dir}/")
        click.echo(f"    full/     # Symlinks to full resolution photos")
        click.echo(f"    web/      # Symlinks to web-optimized photos") 
        click.echo(f"    thumb/    # Generated WebP thumbnails")
        return
    
    # Process collections
    click.echo(f"\nProcessing {len(matched)} photos...")
    
    result = process_dual_photo_collection(
        full_source_dir=full_dir,
        web_source_dir=web_dir,
        output_dir=output_dir,
        collection_name=collection_name
    )
    
    # Show results
    click.echo(f"\nProcessing complete:")
    click.echo(f"  Photos processed: {result['total_processed']}")
    click.echo(f"  Photos skipped:   {result.get('total_skipped', 0)}")
    click.echo(f"  Errors:          {len(result['errors'])}")
    
    if result['errors']:
        click.echo("\nErrors encountered:")
        for error in result['errors'][:10]:
            click.echo(f"  - {error}")
        if len(result['errors']) > 10:
            click.echo(f"  ... and {len(result['errors']) - 10} more errors")
    
    # Show output structure
    click.echo(f"\nOutput created in: {output_dir}")
    click.echo(f"  full/  - {len(list((output_dir / 'full').glob('*')))} symlinks")
    click.echo(f"  web/   - {len(list((output_dir / 'web').glob('*')))} symlinks")
    click.echo(f"  thumb/ - {len(list((output_dir / 'thumb').glob('*')))} thumbnails")