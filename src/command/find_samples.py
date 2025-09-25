import click
from pathlib import Path
import settings
from src.services import fs


@click.command()
@click.option('--pic-source-path-full', '--pic-source', '-s', help='Directory to scan for sample photos')
def find_samples(pic_source_path_full):
    photos_found = fs.ls_full(pic_source_path_full)
    
    if pic_source_path_full is None:
        source_path = Path(settings.PIC_SOURCE_PATH_FULL)
    else:
        source_path = Path(pic_source_path_full)
    
    click.echo(f"Scanning for photos in: {source_path}")
    click.echo(f"Found {len(photos_found)} photos")
    
    for photo in sorted(photos_found):
        click.echo(f"  {photo.relative_to(source_path)}")