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
from src.services.photo_metadata import PhotoMetadataService
from src.services.template_renderer import TemplateRenderer


def build_gallery():
    """Pure function that orchestrates gallery building services.
    
    Returns:
        Dict with build results: {
            'success': bool,
            'photos_processed': int,
            'gallery_generated': bool
        }
    """
    # Create output directory structure
    create_output_directory_structure(Path.cwd())
    
    # Generate photo metadata
    metadata_service = PhotoMetadataService()
    photo_data = metadata_service.generate_json_metadata()
    
    photos_count = len(photo_data['photos'])
    gallery_generated = False
    
    if photo_data['photos']:
        # Render templates
        renderer = TemplateRenderer()
        
        # Generate gallery page
        gallery_template = Path("src/template/gallery.j2.html")
        if gallery_template.exists():
            gallery_html = renderer.render("gallery.j2.html", photo_data)
            renderer.save_html(gallery_html, "prod/site/gallery.html")
            gallery_generated = True
        
        # Generate index page  
        index_template = Path("src/template/index.j2.html")
        if index_template.exists():
            index_html = renderer.render("index.j2.html", photo_data)
            renderer.save_html(index_html, "prod/site/index.html")
    
    return {
        'success': True,
        'photos_processed': photos_count,
        'gallery_generated': gallery_generated
    }


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
    
    # Call the pure build function
    click.echo("Creating output directory structure: prod/site")
    result = build_gallery()
    
    # Report results
    if result['success']:
        click.echo(f"Found {result['photos_processed']} photos")
        if result['gallery_generated']:
            click.echo("Gallery page created: prod/site/gallery.html")
            click.echo("Index page created: prod/site/index.html")
        else:
            click.echo("No photos found to generate gallery")
        click.echo("Build complete!")
    else:
        click.echo("Build failed!")
        return 1