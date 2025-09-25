import click
from pathlib import Path
import settings


@click.command()
@click.option('--pic-source-path-full', '--pic-source', '-s', help='Directory to scan for sample photos')
def find_samples(pic_source_path_full):
    if pic_source_path_full is None:
        pic_source_path_full = settings.PIC_SOURCE_PATH_FULL
    
    source_path = Path(pic_source_path_full)
    click.echo(f"Scanning for photos in: {source_path}")
    
    if not source_path.exists():
        click.echo(f"Directory does not exist: {source_path}")
        return
    
    photo_extensions = {'.jpg', '.jpeg', '.png', '.tiff', '.tif', '.webp'}
    photos_found = []
    
    for file_path in source_path.rglob('*'):
        if file_path.is_file() and file_path.suffix.lower() in photo_extensions:
            photos_found.append(file_path)
    
    click.echo(f"Found {len(photos_found)} photos")
    for photo in sorted(photos_found):
        click.echo(f"  {photo.relative_to(source_path)}")