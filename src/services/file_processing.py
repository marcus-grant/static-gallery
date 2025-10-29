"""File processing service for photo operations."""

import shutil
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, List
from src.models.photo import ProcessedPhoto, GalleryMetadata, PhotoMetadata, MetadataExifData, MetadataFileData, GallerySettings
import settings


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
    from src.services.s3_storage import calculate_file_checksum
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
            
            # Calculate file hash of original source file
            photo_data.file_hash = calculate_file_checksum(photo_path)
                
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
    
    # Generate and save gallery metadata JSON
    if results["photos"]:
        metadata = generate_gallery_metadata(results["photos"], collection_name)
        save_gallery_metadata(metadata, output_dir)
    
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


def generate_gallery_metadata(photos: List[ProcessedPhoto], collection_name: str) -> GalleryMetadata:
    """Generate gallery metadata from processed photos.
    
    Args:
        photos: List of processed photos
        collection_name: Name of the collection
        
    Returns:
        GalleryMetadata dataclass instance
    """
    settings_data = GallerySettings(
        timestamp_offset_hours=getattr(settings, 'TIMESTAMP_OFFSET_HOURS', 0),
        target_timezone_offset_hours=getattr(settings, 'TARGET_TIMEZONE_OFFSET_HOURS', 13),
        web_size=getattr(settings, 'WEB_SIZE', (2048, 2048)),
        thumb_size=getattr(settings, 'THUMB_SIZE', (400, 400)),
        jpeg_quality=getattr(settings, 'JPEG_QUALITY', 85),
        webp_quality=getattr(settings, 'WEBP_QUALITY', 85)
    )
    
    photo_metadata_list = []
    
    for photo in photos:
        # Calculate original and corrected timestamps
        original_timestamp = None
        corrected_timestamp = None
        
        if photo.exif.timestamp:
            corrected_timestamp = photo.exif.timestamp
            # Calculate original by reversing the offset
            offset_hours = getattr(settings, 'TIMESTAMP_OFFSET_HOURS', 0)
            if offset_hours != 0:
                from datetime import timedelta
                original_timestamp = corrected_timestamp - timedelta(hours=offset_hours)
            else:
                original_timestamp = corrected_timestamp
        
        # Generate photo ID from filename without extension
        photo_id = photo.generated_filename.replace('.jpg', '').replace('.jpeg', '') if photo.generated_filename else ""
        
        exif_data = MetadataExifData(
            original_timestamp=original_timestamp.isoformat() if original_timestamp else None,
            corrected_timestamp=corrected_timestamp.isoformat() if corrected_timestamp else None,
            timezone_original="+00:00",  # Assuming UTC in EXIF
            camera={
                "make": photo.camera.make,
                "model": photo.camera.model
            },
            subsecond=photo.exif.subsecond
        )
        
        files_data = MetadataFileData(
            full=f"full/{photo.generated_filename}" if photo.generated_filename else "",
            web=f"web/{photo.generated_filename}" if photo.generated_filename else "",
            thumb=photo.generated_filename.replace('.jpg', '.webp').replace('.jpeg', '.webp') if photo.generated_filename else ""
        )
        
        # Calculate deployment file hash after EXIF modification simulation
        deployment_hash = photo.file_hash or ""
        if photo.file_hash and corrected_timestamp:
            try:
                # Read original image bytes
                with open(photo.path, 'rb') as f:
                    original_image_bytes = f.read()
                
                # Import here to avoid circular imports
                from src.services.s3_storage import modify_exif_in_memory
                
                # Get target timezone setting
                target_timezone_offset_hours = getattr(settings, 'TARGET_TIMEZONE_OFFSET_HOURS', 13)
                
                # Simulate EXIF modification for deployment
                modified_image_bytes = modify_exif_in_memory(
                    original_image_bytes,
                    corrected_timestamp,
                    target_timezone_offset_hours
                )
                
                # Calculate hash of modified image bytes
                import hashlib
                deployment_hash = hashlib.sha256(modified_image_bytes).hexdigest()
                
            except Exception:
                # If EXIF modification fails, fall back to original hash
                deployment_hash = photo.file_hash or ""
        
        photo_meta = PhotoMetadata(
            id=photo_id,
            original_path=str(photo.path),
            file_hash=photo.file_hash or "",
            deployment_file_hash=deployment_hash,
            exif=exif_data,
            files=files_data
        )
        
        photo_metadata_list.append(photo_meta)
    
    return GalleryMetadata(
        schema_version="1.0",
        generated_at=datetime.now(timezone.utc).isoformat(),
        collection=collection_name,
        settings=settings_data,
        photos=photo_metadata_list
    )


def save_gallery_metadata(metadata: GalleryMetadata, output_dir: Path) -> None:
    """Save gallery metadata to JSON file.
    
    Args:
        metadata: Gallery metadata dataclass instance
        output_dir: Directory to save metadata file
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    metadata_file = output_dir / "gallery-metadata.json"
    
    with open(metadata_file, 'w') as f:
        json.dump(metadata.to_dict(), f, indent=2)


def process_dual_photo_collection(
    full_source_dir: Path,
    web_source_dir: Path,
    output_dir: Path,
    collection_name: str,
    batch_size: int = 50
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
    from src.services.s3_storage import calculate_file_checksum
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
    
    # Progress tracking
    total_photos = len(photo_pairs)
    current_photo = 0
    batch_number = 0
    
    # Process photos in batches
    for batch_start in range(0, len(photo_pairs), batch_size):
        batch_number += 1
        batch_end = min(batch_start + batch_size, len(photo_pairs))
        batch_pairs = photo_pairs[batch_start:batch_end]
        
        print(f"Processing batch {batch_number}, photos {batch_start + 1}-{batch_end}")
        
        # Process each photo in this batch
        for full_path, web_path in batch_pairs:
            current_photo += 1
            print(f"Processing photo {current_photo}/{total_photos}: {full_path.name}")
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
                
                # Calculate file hash of original source file
                photo_data.file_hash = calculate_file_checksum(full_path)
                    
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
        
        # Save partial metadata after each batch
        if results["photos"]:
            partial_metadata = generate_gallery_metadata(results["photos"], collection_name)
            partial_filename = f"gallery-metadata.part{batch_number:03d}.json"
            partial_path = output_dir / partial_filename
            with open(partial_path, 'w') as f:
                json.dump(partial_metadata.to_dict(), f, indent=2)
            print(f"Saved partial metadata: {partial_filename}")
    
    # Generate and save gallery metadata JSON
    if results["photos"]:
        metadata = generate_gallery_metadata(results["photos"], collection_name)
        save_gallery_metadata(metadata, output_dir)
    
    return results