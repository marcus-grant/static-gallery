"""
Collection statistics command for Galleria.

Analyzes photo collections for timing, file size, and camera information.
"""
import click
from pathlib import Path
from typing import Optional, Dict, List
import statistics
from collections import defaultdict, Counter
from datetime import datetime
import sys

from src.services.exif import get_datetime_taken, get_camera_info, get_timezone_info


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
    '--processed', '-p',
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    help='Processed photos directory (defaults to prod/pics)'
)
def collection_stats(
    full_source: Optional[Path],
    web_source: Optional[Path],
    processed: Optional[Path]
):
    """Analyze photo collection statistics for timing, file sizes, and camera patterns."""
    # Import settings after click processes arguments
    import settings
    
    # Use provided paths or defaults from settings
    full_dir = full_source or settings.PIC_SOURCE_PATH_FULL
    web_dir = web_source or settings.PIC_SOURCE_PATH_WEB
    processed_dir = processed or (settings.BASE_DIR / 'prod' / 'pics')
    
    click.echo("=== PHOTO COLLECTION ANALYSIS ===\n")
    
    # Analyze original collections
    click.echo("ORIGINAL COLLECTIONS:")
    full_stats = analyze_collection(full_dir, "Full Resolution")
    web_stats = analyze_collection(web_dir, "Web Optimized")
    
    # Analyze processed collection
    click.echo("\nPROCESSED COLLECTION:")
    if processed_dir.exists():
        processed_stats = analyze_processed_collection(processed_dir)
    else:
        click.echo(f"Processed directory not found: {processed_dir}")
        processed_stats = None
    
    # Time analysis across all photos
    click.echo("\nTIME ANALYSIS:")
    analyze_timing_patterns(full_dir, web_dir)
    
    # Camera and photographer analysis
    click.echo("\nCAMERA & PHOTOGRAPHER ANALYSIS:")
    analyze_camera_patterns(full_dir, web_dir)


def analyze_collection(directory: Path, name: str) -> Dict:
    """Analyze a single photo collection directory."""
    if not directory.exists():
        click.echo(f"{name}: Directory not found - {directory}")
        return {}
    
    # Find all image files
    image_files = []
    for ext in ['*.jpg', '*.jpeg', '*.JPG', '*.JPEG']:
        image_files.extend(directory.glob(ext))
    
    if not image_files:
        click.echo(f"{name}: No photos found in {directory}")
        return {}
    
    # Calculate file sizes
    file_sizes = [f.stat().st_size for f in image_files]
    total_size = sum(file_sizes)
    
    click.echo(f"{name}: {len(image_files)} photos")
    click.echo(f"  Total size: {format_bytes(total_size)}")
    click.echo(f"  Average size: {format_bytes(statistics.mean(file_sizes))}")
    click.echo(f"  Median size: {format_bytes(statistics.median(file_sizes))}")
    click.echo(f"  Size range: {format_bytes(min(file_sizes))} - {format_bytes(max(file_sizes))}")
    
    return {
        'count': len(image_files),
        'total_size': total_size,
        'file_sizes': file_sizes,
        'files': image_files
    }


def analyze_processed_collection(processed_dir: Path) -> Dict:
    """Analyze the processed photo collection."""
    full_dir = processed_dir / 'full'
    web_dir = processed_dir / 'web'
    thumb_dir = processed_dir / 'thumb'
    
    dirs = [
        (full_dir, "Symlinked Full"),
        (web_dir, "Symlinked Web"),
        (thumb_dir, "Generated Thumbnails")
    ]
    
    for dir_path, name in dirs:
        if dir_path.exists():
            files = list(dir_path.glob('*'))
            if files:
                if name == "Generated Thumbnails":
                    # Calculate actual thumbnail sizes
                    file_sizes = [f.stat().st_size for f in files if f.is_file()]
                    if file_sizes:
                        total_size = sum(file_sizes)
                        click.echo(f"{name}: {len(files)} files")
                        click.echo(f"  Total size: {format_bytes(total_size)}")
                        click.echo(f"  Average size: {format_bytes(statistics.mean(file_sizes))}")
                else:
                    click.echo(f"{name}: {len(files)} symlinks")
            else:
                click.echo(f"{name}: No files found")
        else:
            click.echo(f"{name}: Directory not found")
    
    return {}


def analyze_timing_patterns(full_dir: Path, web_dir: Path):
    """Analyze timing patterns from EXIF data."""
    timestamps = []
    timezone_info = Counter()
    
    # Collect timestamps from full resolution photos
    image_files = []
    for ext in ['*.jpg', '*.jpeg', '*.JPG', '*.JPEG']:
        image_files.extend(full_dir.glob(ext))
    
    click.echo(f"Extracting EXIF timestamps from {len(image_files)} photos...")
    
    for photo_path in image_files:  # Analyze all photos
        try:
            timestamp = get_datetime_taken(photo_path)
            if timestamp:
                timestamps.append(timestamp)
                
            # Collect timezone information
            tz_info = get_timezone_info(photo_path)
            if tz_info:
                timezone_info[tz_info] += 1
            else:
                timezone_info["No timezone info"] += 1
                
        except Exception as e:
            continue
    
    if not timestamps:
        click.echo("No valid timestamps found in EXIF data")
        return
    
    # Sort timestamps
    timestamps.sort()
    
    # Calculate statistics
    earliest = timestamps[0]
    latest = timestamps[-1]
    duration = latest - earliest
    
    # Find median
    median_timestamp = timestamps[len(timestamps) // 2]
    
    click.echo(f"Earliest photo: {earliest.strftime('%Y-%m-%d %H:%M:%S')}")
    click.echo(f"Latest photo: {latest.strftime('%Y-%m-%d %H:%M:%S')}")
    click.echo(f"Median timestamp: {median_timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
    click.echo(f"Total duration: {duration}")
    click.echo(f"Sample size: {len(timestamps)} photos analyzed")
    
    # Analyze time gaps
    if len(timestamps) > 1:
        gaps = []
        for i in range(1, len(timestamps)):
            gap = (timestamps[i] - timestamps[i-1]).total_seconds()
            gaps.append(gap)
        
        avg_gap = statistics.mean(gaps)
        max_gap = max(gaps)
        
        click.echo(f"Average time between photos: {avg_gap:.1f} seconds")
        click.echo(f"Longest gap between photos: {max_gap:.1f} seconds ({max_gap/60:.1f} minutes)")
    
    # Report timezone information
    click.echo("\nTIMEZONE INFORMATION:")
    for tz, count in timezone_info.most_common():
        percentage = (count / len(image_files)) * 100
        click.echo(f"  {tz}: {count} photos ({percentage:.1f}%)")


def analyze_camera_patterns(full_dir: Path, web_dir: Path):
    """Analyze camera and photographer patterns from filenames and EXIF."""
    # Analyze filename patterns
    filename_patterns = Counter()
    camera_models = Counter()
    
    # Collect all image files
    all_files = []
    for directory in [full_dir, web_dir]:
        if directory.exists():
            for ext in ['*.jpg', '*.jpeg', '*.JPG', '*.JPEG']:
                all_files.extend([(f, directory.name) for f in directory.glob(ext)])
    
    click.echo(f"Analyzing filename patterns from {len(all_files)} photos...")
    
    for photo_path, source in all_files:  # Analyze all photos
        # Analyze filename patterns
        filename = photo_path.name
        
        # Extract filename prefixes (common camera naming patterns)
        if '_' in filename:
            prefix = filename.split('_')[0]
        elif filename[0].isdigit():
            # Find where letters start
            for i, char in enumerate(filename):
                if char.isalpha():
                    prefix = filename[:i+1] if i > 0 else filename[:3]
                    break
            else:
                prefix = filename[:4]  # All digits
        else:
            prefix = filename[:4]
        
        filename_patterns[f"{prefix}*"] += 1
        
        # Extract camera info from EXIF
        try:
            camera_info = get_camera_info(photo_path)
            if camera_info:
                make, model = camera_info
                if make and model:
                    camera_key = f"{make} {model}"
                    camera_models[camera_key] += 1
        except Exception:
            continue
    
    # Report filename patterns
    click.echo("\nFILENAME PATTERNS:")
    for pattern, count in filename_patterns.most_common():
        click.echo(f"  {pattern}: {count} photos")
    
    # Report camera models
    click.echo("\nCAMERA MODELS:")
    for camera, count in camera_models.most_common():
        click.echo(f"  {camera}: {count} photos")
    
    # Analyze for potential multiple photographers
    if len(filename_patterns) > 1:
        click.echo("\nMULTIPLE NAMING PATTERNS DETECTED:")
        click.echo("This suggests photos from multiple cameras or photographers")
        for pattern, count in filename_patterns.most_common():
            percentage = (count / sum(filename_patterns.values())) * 100
            click.echo(f"  {pattern}: {percentage:.1f}% of analyzed photos")


def format_bytes(bytes_val: int) -> str:
    """Format bytes in human readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_val < 1024.0:
            return f"{bytes_val:.1f} {unit}"
        bytes_val /= 1024.0
    return f"{bytes_val:.1f} TB"