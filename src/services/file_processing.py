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


def process_photo_collection(source_dir: Path, output_dir: Path, 
                           collection_name: str) -> dict:
    """Process a collection of photos - extract EXIF, generate filenames, create links and thumbnails.
    
    Args:
        source_dir: Directory containing original photos
        output_dir: Base output directory for processed files
        collection_name: Name for this photo collection
        
    Returns:
        Dictionary with processing results and any errors
    """
    from src.services import fs, exif
    from src.services.filename_service import generate_photo_filename
    from src.models.photo import photo_from_exif_service
    
    results = {
        "total_processed": 0,
        "errors": [],
        "photos": []
    }
    
    # Get all image files
    photo_files = fs.ls_full(str(source_dir))
    
    for photo_path in photo_files:
        try:
            # Extract metadata
            timestamp = exif.get_datetime_taken(photo_path)
            camera_info = exif.get_camera_info(photo_path)
            exif_data = exif.extract_exif_data(photo_path)
            subsecond = exif.get_subsecond_precision(photo_path)
            
            # Detect edge cases
            edge_cases = []
            if timestamp is None:
                edge_cases.append("missing_exif")
            
            # Create ProcessedPhoto
            photo_data = photo_from_exif_service(
                path=photo_path,
                timestamp=timestamp,
                camera_info=camera_info or {"make": None, "model": None},
                exif_data=exif_data,
                subsecond=subsecond,
                edge_cases=edge_cases
            )
                
            # Generate chronological filename
            photo_data.collection = collection_name
            photo_data.generated_filename = generate_photo_filename(
                photo_data, collection_name
            )
            
            # Create output directories
            full_output = output_dir / "full"
            thumb_output = output_dir / "thumb"
            
            # Link photo with new filename
            linked_path = link_photo_with_filename(photo_data, full_output)
            
            # Create thumbnail
            thumb_path = thumb_output / photo_data.generated_filename.replace(
                photo_path.suffix, ".webp"
            )
            create_thumbnail(photo_path, thumb_path)
            
            results["photos"].append(photo_data)
            results["total_processed"] += 1
            
        except Exception as e:
            results["errors"].append(f"{photo_path.name}: {str(e)}")
    
    return results