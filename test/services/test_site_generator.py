"""Tests for site generator service."""
import pytest
from pathlib import Path


def test_check_source_directory_exists():
    """Test checking if source directory exists."""
    from src.services.site_generator import check_source_directory
    
    # Create a temporary directory
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        base_dir = Path(tmpdir)
        source_dir = base_dir / "prod" / "pics"
        
        # Should return False when directory doesn't exist
        result = check_source_directory(base_dir)
        assert result is False
        
        # Create the directory structure
        source_dir.mkdir(parents=True)
        
        # Should return True when directory exists
        result = check_source_directory(base_dir)
        assert result is True


def test_check_source_subdirectories():
    """Test checking if source subdirectories exist."""
    from src.services.site_generator import check_source_subdirectories
    
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        base_dir = Path(tmpdir)
        source_dir = base_dir / "prod" / "pics"
        
        # Should return empty dict when directory doesn't exist
        result = check_source_subdirectories(base_dir)
        assert result == {'full': False, 'web': False, 'thumb': False}
        
        # Create main directory
        source_dir.mkdir(parents=True)
        
        # Should still return False for subdirectories
        result = check_source_subdirectories(base_dir)
        assert result == {'full': False, 'web': False, 'thumb': False}
        
        # Create subdirectories
        (source_dir / "full").mkdir()
        (source_dir / "web").mkdir()
        (source_dir / "thumb").mkdir()
        
        # Should return True for all subdirectories
        result = check_source_subdirectories(base_dir)
        assert result == {'full': True, 'web': True, 'thumb': True}


def test_create_output_directory_structure():
    """Test creating output directory structure."""
    from src.services.site_generator import create_output_directory_structure
    
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        base_dir = Path(tmpdir)
        
        # Create output structure
        result = create_output_directory_structure(base_dir)
        
        # Check directories were created
        output_dir = base_dir / "prod" / "site"
        assert output_dir.exists()
        assert (output_dir / "css").exists()
        assert (output_dir / "js").exists()
        
        # Should return dict with created directories
        assert result['created']
        assert 'prod/site' in result['message']
        
        # Running again should not recreate
        result2 = create_output_directory_structure(base_dir)
        assert not result2['created']
        assert 'exists' in result2['message'].lower()