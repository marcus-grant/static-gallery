import click
from pathlib import Path
import settings
from src.services import fs, exif


@click.command()
@click.option('--pic-source-path-full', '--pic-source', '-s', help='Directory to scan for sample photos')
@click.option('--show-bursts', is_flag=True, help='Show burst sequences')
@click.option('--show-conflicts', is_flag=True, help='Show timestamp conflicts from different cameras')
@click.option('--show-missing-exif', is_flag=True, help='Show photos missing EXIF data')
@click.option('--show-camera-diversity', is_flag=True, help='Show camera diversity breakdown')
def find_samples(pic_source_path_full, show_bursts, show_conflicts, show_missing_exif, show_camera_diversity):
    photos_found = fs.ls_full(pic_source_path_full)
    
    if pic_source_path_full is None:
        source_path = Path(settings.PIC_SOURCE_PATH_FULL)
    else:
        source_path = Path(pic_source_path_full)
    
    click.echo(f"Scanning for photos in: {source_path}")
    click.echo(f"Found {len(photos_found)} photos")
    
    # Show regular list if no filters specified
    if not any([show_bursts, show_conflicts, show_missing_exif, show_camera_diversity]):
        for photo in sorted(photos_found):
            click.echo(f"  {photo.relative_to(source_path)}")
        return
    
    # Show burst sequences
    if show_bursts:
        click.echo("\nAnalyzing burst sequences...")
        sorted_photos = exif.sort_photos_chronologically(photos_found)
        burst_sequences = exif.detect_burst_sequences(sorted_photos)
        
        if burst_sequences:
            click.echo(f"Found {len(burst_sequences)} burst sequence(s):")
            for i, burst in enumerate(burst_sequences, 1):
                click.echo(f"\nBurst sequence ({len(burst)} photos):")
                for photo in burst:
                    click.echo(f"  {photo.relative_to(source_path)}")
        else:
            click.echo("No burst sequences found.")
    
    # Show timestamp conflicts
    if show_conflicts:
        click.echo("\nAnalyzing timestamp conflicts...")
        conflicts = exif.find_timestamp_conflicts(photos_found)
        
        if conflicts:
            click.echo(f"Found {len(conflicts)} timestamp conflict(s):")
            for i, conflict_group in enumerate(conflicts, 1):
                click.echo(f"\nConflict group {i} ({len(conflict_group)} photos):")
                for photo in conflict_group:
                    camera_info = exif.get_camera_info(photo)
                    camera = f"{camera_info.get('make', 'Unknown')} {camera_info.get('model', '')}"
                    click.echo(f"  {photo.relative_to(source_path)} - {camera}")
        else:
            click.echo("No timestamp conflicts found.")
    
    # Show missing EXIF data
    if show_missing_exif:
        click.echo("\nChecking for missing EXIF data...")
        missing_exif = exif.find_missing_exif_photos(photos_found)
        
        if missing_exif:
            click.echo(f"Found {len(missing_exif)} photo(s) without EXIF timestamps:")
            for photo in missing_exif:
                click.echo(f"  {photo.relative_to(source_path)}")
        else:
            click.echo("All photos have EXIF timestamps.")
    
    # Show camera diversity
    if show_camera_diversity:
        click.echo("\nAnalyzing camera diversity...")
        camera_groups = exif.get_camera_diversity_samples(photos_found)
        
        click.echo(f"Found {len(camera_groups)} different camera(s):")
        for (make, model), photos in sorted(camera_groups.items()):
            camera = f"{make or 'Unknown'} {model or 'Unknown'}".strip()
            if camera == "":
                camera = "Unknown camera"
            click.echo(f"\n{camera}: {len(photos)} photos")
            # Show first few examples
            for photo in photos[:3]:
                click.echo(f"  {photo.relative_to(source_path)}")
            if len(photos) > 3:
                click.echo(f"  ... and {len(photos) - 3} more")