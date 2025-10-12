"""Photo collection validation services."""
from pathlib import Path
from typing import Dict, List, Tuple, Set


def get_photo_filename_mapping(directory: Path) -> Dict[str, Path]:
    """Get mapping of photo filenames (without extension) to full paths.
    
    Args:
        directory: Directory containing photos
        
    Returns:
        Dict mapping filename stems to full paths
    """
    from src.services import fs
    
    photos = fs.ls_full(str(directory))
    mapping = {}
    
    for photo_path in photos:
        stem = photo_path.stem  # filename without extension
        mapping[stem] = photo_path
    
    return mapping


def validate_matching_collections(
    full_dir: Path, 
    web_dir: Path
) -> Tuple[List[str], List[str], List[str]]:
    """Validate that full and web collections have matching photos.
    
    Args:
        full_dir: Directory containing full resolution photos
        web_dir: Directory containing web-optimized photos
        
    Returns:
        Tuple of (matched_stems, full_only_stems, web_only_stems)
    """
    full_mapping = get_photo_filename_mapping(full_dir)
    web_mapping = get_photo_filename_mapping(web_dir)
    
    full_stems = set(full_mapping.keys())
    web_stems = set(web_mapping.keys())
    
    matched = sorted(full_stems & web_stems)
    full_only = sorted(full_stems - web_stems)
    web_only = sorted(web_stems - full_stems)
    
    return matched, full_only, web_only


def get_matched_photo_pairs(
    full_dir: Path,
    web_dir: Path
) -> List[Tuple[Path, Path]]:
    """Get pairs of matching photos from full and web directories.
    
    Args:
        full_dir: Directory containing full resolution photos
        web_dir: Directory containing web-optimized photos
        
    Returns:
        List of (full_path, web_path) tuples for matching photos
    """
    full_mapping = get_photo_filename_mapping(full_dir)
    web_mapping = get_photo_filename_mapping(web_dir)
    
    pairs = []
    for stem in sorted(full_mapping.keys()):
        if stem in web_mapping:
            pairs.append((full_mapping[stem], web_mapping[stem]))
    
    return pairs