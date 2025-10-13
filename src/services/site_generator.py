"""Site generator service for building static photo gallery."""
from pathlib import Path
from typing import Dict


def check_source_directory(base_dir: Path) -> bool:
    """Check if source directory exists.
    
    Args:
        base_dir: Base directory to check from
        
    Returns:
        True if prod/pics exists, False otherwise
    """
    source_dir = base_dir / "prod" / "pics"
    return source_dir.exists()


def check_source_subdirectories(base_dir: Path) -> Dict[str, bool]:
    """Check if source subdirectories exist.
    
    Args:
        base_dir: Base directory to check from
        
    Returns:
        Dict with subdirectory names and existence status
    """
    source_dir = base_dir / "prod" / "pics"
    subdirs = ['full', 'web', 'thumb']
    
    result = {}
    for subdir in subdirs:
        subdir_path = source_dir / subdir
        result[subdir] = subdir_path.exists()
    
    return result


def create_output_directory_structure(base_dir: Path) -> Dict[str, any]:
    """Create output directory structure for generated site.
    
    Args:
        base_dir: Base directory to create structure in
        
    Returns:
        Dict with 'created' status and 'message'
    """
    output_dir = base_dir / "prod" / "site"
    subdirs = ["css", "js"]
    
    # Check if main directory already exists
    if output_dir.exists():
        return {
            'created': False,
            'message': 'Output directory already exists'
        }
    
    # Create main directory and subdirectories
    output_dir.mkdir(parents=True)
    for subdir in subdirs:
        (output_dir / subdir).mkdir()
    
    return {
        'created': True,
        'message': f'Created output directory: prod/site'
    }