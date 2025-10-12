"""File processing service for photo operations."""

import shutil
from pathlib import Path
from typing import Optional, Dict, List
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
    
    # Check if symlink already exists
    if new_path.exists():
        if new_path.is_symlink() and new_path.resolve() == photo.path.absolute():
            # Same symlink already exists, that's OK
            return new_path
        else:
            # Different file or symlink exists with same name
            raise FileExistsError(f"File already exists: {new_path}")
    
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
    
    # Track existing filenames to handle burst sequences
    existing_filenames = set()
    
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
                photo_data, collection_name, existing_filenames
            )
            existing_filenames.add(photo_data.generated_filename)
            
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


def is_processing_needed(full_path: Path, web_path: Path, output_dir: Path, generated_filename: str) -> bool:
    """Check if processing is needed for a photo pair.
    
    Returns True if any output is missing or source files are newer than outputs.
    """
    # Define expected output paths
    full_output = output_dir / "full" / generated_filename
    web_output = output_dir / "web" / generated_filename
    thumb_output = output_dir / "thumb" / generated_filename.replace(full_path.suffix, ".webp")
    
    # Check if all outputs exist
    if not (full_output.exists() and web_output.exists() and thumb_output.exists()):
        return True
    
    # Check if source files are newer than outputs
    full_mtime = full_path.stat().st_mtime
    web_mtime = web_path.stat().st_mtime
    
    output_times = [
        full_output.stat().st_mtime,
        web_output.stat().st_mtime,
        thumb_output.stat().st_mtime
    ]
    
    # If any source is newer than any output, processing is needed
    min_output_time = min(output_times)
    if full_mtime > min_output_time or web_mtime > min_output_time:
        return True
    
    return False


def process_dual_photo_collection(
    full_source_dir: Path,
    web_source_dir: Path,
    output_dir: Path,
    collection_name: str
) -> dict:
    """Process dual photo collections - full resolution and web-optimized versions.
    
    Creates symlinks for both full and web versions, generates thumbnails from web versions.
    
    Args:
        full_source_dir: Directory containing full resolution photos
        web_source_dir: Directory containing web-optimized photos
        output_dir: Base output directory for processed files
        collection_name: Name for this photo collection
        
    Returns:
        Dictionary with processing results and any errors
    """
    from src.services import fs, exif
    from src.services.filename_service import generate_photo_filename
    from src.services.photo_validation import get_matched_photo_pairs, validate_matching_collections
    from src.models.photo import photo_from_exif_service
    
    results = {
        "total_processed": 0,
        "total_skipped": 0,
        "errors": [],
        "photos": [],
        "validation": {}
    }
    
    # Validate collections match
    matched, full_only, web_only = validate_matching_collections(full_source_dir, web_source_dir)
    results["validation"] = {
        "matched_count": len(matched),
        "full_only": full_only,
        "web_only": web_only
    }
    
    if full_only:
        results["errors"].append(f"Photos only in full collection: {', '.join(full_only[:5])}" + 
                                ("..." if len(full_only) > 5 else ""))
    if web_only:
        results["errors"].append(f"Photos only in web collection: {', '.join(web_only[:5])}" + 
                                ("..." if len(web_only) > 5 else ""))
    
    # Get matched pairs
    photo_pairs = get_matched_photo_pairs(full_source_dir, web_source_dir)
    
    # Track existing filenames to handle burst sequences
    existing_filenames = set()
    
    for full_path, web_path in photo_pairs:
        try:
            # Extract metadata from full resolution version
            timestamp = exif.get_datetime_taken(full_path)
            camera_info = exif.get_camera_info(full_path)
            exif_data = exif.extract_exif_data(full_path)
            subsecond = exif.get_subsecond_precision(full_path)
            
            # Detect edge cases
            edge_cases = []
            if timestamp is None:
                edge_cases.append("missing_exif")
            
            # Create ProcessedPhoto
            photo_data = photo_from_exif_service(
                path=full_path,
                timestamp=timestamp,
                camera_info=camera_info or {"make": None, "model": None},
                exif_data=exif_data,
                subsecond=subsecond,
                edge_cases=edge_cases
            )
                
            # Generate chronological filename
            photo_data.collection = collection_name
            photo_data.generated_filename = generate_photo_filename(
                photo_data, collection_name, existing_filenames
            )
            existing_filenames.add(photo_data.generated_filename)
            
            # Check if processing is needed
            if not is_processing_needed(full_path, web_path, output_dir, photo_data.generated_filename):
                results["total_skipped"] += 1
                continue
            
            # Create output directories
            full_output = output_dir / "full"
            web_output = output_dir / "web"
            thumb_output = output_dir / "thumb"
            
            # Link full resolution photo with new filename
            full_linked = link_photo_with_filename(photo_data, full_output)
            
            # Link web version with same chronological filename
            web_photo = ProcessedPhoto(
                path=web_path,
                filename=web_path.name,
                file_size=web_path.stat().st_size,
                camera=photo_data.camera,
                exif=photo_data.exif,
                edge_cases=photo_data.edge_cases,
                collection=photo_data.collection,
                generated_filename=photo_data.generated_filename
            )
            web_linked = link_photo_with_filename(web_photo, web_output)
            
            # Create thumbnail from web version
            thumb_filename = photo_data.generated_filename.replace(
                full_path.suffix, ".webp"
            )
            thumb_path = thumb_output / thumb_filename
            create_thumbnail(web_path, thumb_path)
            
            results["photos"].append(photo_data)
            results["total_processed"] += 1
            
        except Exception as e:
            results["errors"].append(f"{full_path.name}: {str(e)}")
    
    return results