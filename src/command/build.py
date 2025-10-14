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
    
    # Generate photo metadata
    click.echo("Scanning photos...")
    metadata_service = PhotoMetadataService()
    photo_data = metadata_service.generate_json_metadata()
    
    if photo_data['photos']:
        click.echo(f"Found {len(photo_data['photos'])} photos")
        
        # Check if template exists before rendering
        template_path = Path("src/template/gallery.j2.html")
        if template_path.exists():
            # Render and save gallery
            click.echo("Generating gallery...")
            renderer = TemplateRenderer()
            gallery_html = renderer.render("gallery.j2.html", photo_data)
            renderer.save_html(gallery_html, "prod/site/gallery.html")
            click.echo("Gallery page created: prod/site/gallery.html")
        else:
            click.echo("Template not found: src/template/gallery.j2.html")
    else:
        click.echo("No photos found to generate gallery")
    
    click.echo("Build complete!")