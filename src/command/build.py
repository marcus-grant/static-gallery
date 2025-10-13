"""
Build command for Galleria.

Generates static website from processed photos.
"""
import click
from pathlib import Path
from src.services.site_generator import (
    check_source_directory, 
    check_source_subdirectories,
    create_output_directory_structure
)


@click.command()
def build():
    """Build static photo gallery site from processed photos."""
    click.echo("Generating static site...")
    
    # Check source directory
    base_dir = Path.cwd()
    click.echo("Checking source directory: prod/pics")
    
    if not check_source_directory(base_dir):
        click.echo("Source directory not found: prod/pics")
    else:
        # Check subdirectories
        subdirs = check_source_subdirectories(base_dir)
        missing = [name for name, exists in subdirs.items() if not exists]
        
        if missing:
            click.echo(f"Missing subdirectories: {', '.join(missing)}")
        else:
            click.echo("All source directories found")
    
    # Create output directory structure
    click.echo("Creating output directory structure: prod/site")
    result = create_output_directory_structure(base_dir)
    
    if result['created']:
        click.echo("Created directory structure: prod/site with css/ and js/ subdirectories")
    else:
        click.echo("Output directory already exists: prod/site")
    
    click.echo("Build complete!")