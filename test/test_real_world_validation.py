import pytest
import subprocess
import sys
from pathlib import Path


@pytest.mark.realworld
class TestRealWorldValidation:
    """Real-world validation tests using actual photo collections.
    
    Run with: pytest -m realworld
    Skipped by default to avoid running in CI/CD.
    """
    
    def test_skip_if_no_real_photos(self):
        """Skip if settings.local.py doesn't exist or photo path is invalid"""
        project_root = Path(__file__).parent.parent
        sys.path.insert(0, str(project_root))
        
        try:
            import settings
            if not hasattr(settings, 'PIC_SOURCE_PATH_FULL'):
                pytest.skip("PIC_SOURCE_PATH_FULL not configured in settings.local.py")
            if not settings.PIC_SOURCE_PATH_FULL.exists():
                pytest.skip(f"Real photo path doesn't exist: {settings.PIC_SOURCE_PATH_FULL}")
            
            # Count actual image files
            image_files = list(settings.PIC_SOURCE_PATH_FULL.rglob("*.jpg")) + \
                         list(settings.PIC_SOURCE_PATH_FULL.rglob("*.jpeg")) + \
                         list(settings.PIC_SOURCE_PATH_FULL.rglob("*.png"))
            
            if len(image_files) < 5:
                pytest.skip(f"Not enough photos for validation: {len(image_files)} found")
        finally:
            if str(project_root) in sys.path:
                sys.path.remove(str(project_root))
    
    def test_real_camera_detection(self):
        """Test that real cameras are properly detected"""
        project_root = Path(__file__).parent.parent
        sys.path.insert(0, str(project_root))
        
        try:
            import settings
            if not settings.PIC_SOURCE_PATH_FULL.exists():
                pytest.skip("No real photos configured")
            photo_path = str(settings.PIC_SOURCE_PATH_FULL)
        finally:
            if str(project_root) in sys.path:
                sys.path.remove(str(project_root))
        
        # Run find-samples with camera diversity
        result = subprocess.run(
            [sys.executable, "manage.py", "find-samples", "-s", photo_path, "--show-camera-diversity"],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        assert result.returncode == 0, f"Command failed: {result.stderr}"
        
        # Should find at least one camera
        assert "different camera(s):" in result.stdout
        
        # Common camera manufacturers that might appear
        expected_brands = ['Canon', 'Nikon', 'Sony', 'Apple', 'Samsung', 'Fujifilm', 'Olympus', 'Panasonic']
        found_brands = []
        
        for brand in expected_brands:
            if brand in result.stdout:
                found_brands.append(brand)
        
        print(f"\nDetected camera brands: {found_brands}")
        
        # Should detect at least some real camera brands (not just "Unknown")
        assert len(found_brands) > 0, "No known camera brands detected in real photos"
    
    def test_real_burst_detection(self):
        """Test burst detection on real photo sequences"""
        project_root = Path(__file__).parent.parent
        sys.path.insert(0, str(project_root))
        
        try:
            import settings
            if not settings.PIC_SOURCE_PATH_FULL.exists():
                pytest.skip("No real photos configured")
            photo_path = str(settings.PIC_SOURCE_PATH_FULL)
        finally:
            if str(project_root) in sys.path:
                sys.path.remove(str(project_root))
        
        # Run find-samples with burst detection
        result = subprocess.run(
            [sys.executable, "manage.py", "find-samples", "-s", photo_path, "--show-bursts"],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        assert result.returncode == 0, f"Command failed: {result.stderr}"
        
        if "Found 0 burst sequence(s)" in result.stdout:
            print("\nNo burst sequences detected in real photos")
            # This might be expected if the collection doesn't have bursts
        else:
            print(f"\nBurst detection results from real photos:")
            output_lines = result.stdout.split('\n')
            for line in output_lines:
                if 'burst sequence' in line.lower() or 'photos):' in line:
                    print(f"  {line}")
    
    def test_real_timestamp_conflicts(self):
        """Test timestamp conflict detection with real multi-photographer scenarios"""
        project_root = Path(__file__).parent.parent
        sys.path.insert(0, str(project_root))
        
        try:
            import settings
            if not settings.PIC_SOURCE_PATH_FULL.exists():
                pytest.skip("No real photos configured")
            photo_path = str(settings.PIC_SOURCE_PATH_FULL)
        finally:
            if str(project_root) in sys.path:
                sys.path.remove(str(project_root))
        
        # Run find-samples with conflict detection
        result = subprocess.run(
            [sys.executable, "manage.py", "find-samples", "-s", photo_path, "--show-conflicts"],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        assert result.returncode == 0, f"Command failed: {result.stderr}"
        
        if "Found 0 timestamp conflict(s)" in result.stdout:
            print("\nNo timestamp conflicts detected in real photos")
        else:
            print(f"\nTimestamp conflict results from real photos:")
            output_lines = result.stdout.split('\n')
            in_conflict_section = False
            for line in output_lines:
                if 'timestamp conflict' in line.lower():
                    in_conflict_section = True
                    print(f"  {line}")
                elif in_conflict_section and (line.strip() == "" or "Checking for" in line):
                    in_conflict_section = False
                elif in_conflict_section:
                    print(f"  {line}")
    
    def test_real_missing_exif_detection(self):
        """Test missing EXIF detection on real photos"""
        project_root = Path(__file__).parent.parent
        sys.path.insert(0, str(project_root))
        
        try:
            import settings
            if not settings.PIC_SOURCE_PATH_FULL.exists():
                pytest.skip("No real photos configured")
            photo_path = str(settings.PIC_SOURCE_PATH_FULL)
        finally:
            if str(project_root) in sys.path:
                sys.path.remove(str(project_root))
        
        # Run find-samples with missing EXIF detection
        result = subprocess.run(
            [sys.executable, "manage.py", "find-samples", "-s", photo_path, "--show-missing-exif"],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        assert result.returncode == 0, f"Command failed: {result.stderr}"
        
        if "All photos have EXIF timestamps" in result.stdout:
            print("\nAll real photos have EXIF timestamps")
        else:
            # Extract count of photos without EXIF
            output_lines = result.stdout.split('\n')
            for line in output_lines:
                if "photo(s) without EXIF timestamps:" in line:
                    print(f"\n{line}")
                    break
    
    def test_real_photo_chronological_sorting(self):
        """Test that real photos are sorted chronologically"""
        project_root = Path(__file__).parent.parent
        sys.path.insert(0, str(project_root))
        
        try:
            import settings
            if not settings.PIC_SOURCE_PATH_FULL.exists():
                pytest.skip("No real photos configured")
            photo_path = str(settings.PIC_SOURCE_PATH_FULL)
        finally:
            if str(project_root) in sys.path:
                sys.path.remove(str(project_root))
        
        # Run basic find-samples to get all photos
        result = subprocess.run(
            [sys.executable, "manage.py", "find-samples", "-s", photo_path],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        assert result.returncode == 0, f"Command failed: {result.stderr}"
        
        # Extract photo count
        output_lines = result.stdout.strip().split('\n')
        found_line = next(line for line in output_lines if "Found" in line and "photos" in line)
        photo_count = int(found_line.split()[1])
        
        print(f"\nReal photo collection summary:")
        print(f"Total photos found: {photo_count}")
        
        # List first few and last few photos to verify chronological sorting
        photo_lines = [line.strip() for line in output_lines if line.strip() and not any(
            keyword in line for keyword in ["Scanning", "Found", "photos"]
        )]
        
        if len(photo_lines) > 0:
            print(f"First few photos (chronologically):")
            for i, photo in enumerate(photo_lines[:5]):
                print(f"  {i+1}. {photo}")
            
            if len(photo_lines) > 10:
                print(f"Last few photos (chronologically):")
                for i, photo in enumerate(photo_lines[-3:]):
                    print(f"  {len(photo_lines)-2+i}. {photo}")
    
    def test_iphone_photo_detection(self):
        """Test detection of iPhone/smartphone photos if present"""
        project_root = Path(__file__).parent.parent
        sys.path.insert(0, str(project_root))
        
        try:
            import settings
            if not settings.PIC_SOURCE_PATH_FULL.exists():
                pytest.skip("No real photos configured")
            photo_path = str(settings.PIC_SOURCE_PATH_FULL)
        finally:
            if str(project_root) in sys.path:
                sys.path.remove(str(project_root))
        
        # Run find-samples with camera diversity
        result = subprocess.run(
            [sys.executable, "manage.py", "find-samples", "-s", photo_path, "--show-camera-diversity"],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        assert result.returncode == 0, f"Command failed: {result.stderr}"
        
        smartphone_indicators = ['iPhone', 'Apple', 'Samsung', 'Pixel', 'OnePlus', 'Huawei']
        found_smartphones = []
        
        for indicator in smartphone_indicators:
            if indicator in result.stdout:
                found_smartphones.append(indicator)
        
        if found_smartphones:
            print(f"\nSmartphone cameras detected: {found_smartphones}")
        else:
            print("\nNo smartphone cameras detected in collection")
    
    def test_validate_edge_cases_in_real_data(self):
        """Validate that edge cases are properly handled in real data"""
        project_root = Path(__file__).parent.parent
        sys.path.insert(0, str(project_root))
        
        try:
            import settings
            if not settings.PIC_SOURCE_PATH_FULL.exists():
                pytest.skip("No real photos configured")
            photo_path = str(settings.PIC_SOURCE_PATH_FULL)
        finally:
            if str(project_root) in sys.path:
                sys.path.remove(str(project_root))
        
        # Run all filters to see what edge cases exist in real data
        result = subprocess.run(
            [sys.executable, "manage.py", "find-samples",
             "-s", photo_path,
             "--show-bursts",
             "--show-conflicts", 
             "--show-missing-exif",
             "--show-camera-diversity"],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        assert result.returncode == 0, f"Command failed: {result.stderr}"
        
        print(f"\nReal-world edge case summary:")
        
        # Parse results for different edge cases
        output = result.stdout
        
        # Count burst sequences
        if "burst sequence(s):" in output:
            burst_count = 0
            for line in output.split('\n'):
                if "Found" in line and "burst sequence(s):" in line:
                    burst_count = int(line.split()[1])
                    break
            print(f"Burst sequences found: {burst_count}")
        
        # Count timestamp conflicts
        if "timestamp conflict(s):" in output:
            conflict_count = 0
            for line in output.split('\n'):
                if "Found" in line and "timestamp conflict(s):" in line:
                    conflict_count = int(line.split()[1])
                    break
            print(f"Timestamp conflicts found: {conflict_count}")
        
        # Count missing EXIF
        if "without EXIF timestamps:" in output:
            missing_count = 0
            for line in output.split('\n'):
                if "Found" in line and "without EXIF timestamps:" in line:
                    missing_count = int(line.split()[1])
                    break
            print(f"Photos without EXIF: {missing_count}")
        
        # Count cameras
        if "different camera(s):" in output:
            camera_count = 0
            for line in output.split('\n'):
                if "Found" in line and "different camera(s):" in line:
                    camera_count = int(line.split()[1])
                    break
            print(f"Different cameras found: {camera_count}")