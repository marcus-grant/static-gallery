"""File processing service for photo operations."""

import shutil
from pathlib import Path
from src.models.photo import ProcessedPhoto


def link_photo_with_filename(photo: ProcessedPhoto, output_dir: Path) -> Path:
    """Create symlink to photo in output directory with generated chronological filename.
    
    Note: Currently creates symlinks for storage efficiency. Future versions may
    support copying or remote storage uploads.
    
    Args:
        photo: ProcessedPhoto with generated_filename set
        output_dir: Directory to create symlink in
        
    Returns:
        Path to symlink
        
    Raises:
        ValueError: If no generated_filename
        FileNotFoundError: If source file doesn't exist
    """
    if not photo.generated_filename:
        raise ValueError("No generated filename for photo")
    
    if not photo.path.exists():
        raise FileNotFoundError(f"Source file not found: {photo.path}")
    
    output_dir.mkdir(parents=True, exist_ok=True)
    new_path = output_dir / photo.generated_filename
    
    # Create symlink to original file
    new_path.symlink_to(photo.path.absolute())
    
    return new_path


# Thumbnail settings
THUMBNAIL_SIZE = 400  # Max dimension for thumbnails
THUMBNAIL_QUALITY = 85  # WebP quality


def create_thumbnail(source_path: Path, thumb_path: Path) -> bool:
    """Create a WebP thumbnail from source image.
    
    Args:
        source_path: Path to source image
        thumb_path: Path for output thumbnail
        
    Returns:
        True if successful, False otherwise
    """
    try:
        from PIL import Image
        
        # Create parent directory if needed
        thumb_path.parent.mkdir(parents=True, exist_ok=True)
        
        with Image.open(source_path) as img:
            # Calculate thumbnail size maintaining aspect ratio
            img.thumbnail((THUMBNAIL_SIZE, THUMBNAIL_SIZE), Image.Resampling.LANCZOS)
            
            # Save as WebP
            img.save(thumb_path, "WEBP", quality=THUMBNAIL_QUALITY)
            
        return True
    except Exception:
        return False