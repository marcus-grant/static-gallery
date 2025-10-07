import pytest
import time
import os
from click.testing import CliRunner
from src.command.find_samples import find_samples
import settings

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False


@pytest.mark.realworld
class TestPerformanceRealPhotos:
    """Performance tests using real photo collections.
    
    Run with: pytest -m realworld
    Skipped by default to avoid running in CI/CD.
    """
    
    def test_skip_if_no_real_photos(self):
        """Skip if settings.local.py doesn't exist or photo path is invalid"""
        if not settings.PIC_SOURCE_PATH_FULL.exists():
            pytest.skip(f"Real photo path doesn't exist: {settings.PIC_SOURCE_PATH_FULL}")
        
        # Count actual image files
        image_files = list(settings.PIC_SOURCE_PATH_FULL.rglob("*.jpg")) + \
                     list(settings.PIC_SOURCE_PATH_FULL.rglob("*.jpeg")) + \
                     list(settings.PIC_SOURCE_PATH_FULL.rglob("*.png"))
        
        if len(image_files) < 10:
            pytest.skip(f"Not enough photos for performance testing: {len(image_files)} found")
    
    def test_performance_basic_scan(self):
        """Test basic photo scanning performance"""
        if not settings.PIC_SOURCE_PATH_FULL.exists():
            pytest.skip("No real photos configured")
        
        if not HAS_PSUTIL:
            pytest.skip("psutil not available for memory monitoring")
        
        runner = CliRunner()
        
        # Measure memory before
        process = psutil.Process(os.getpid())
        memory_before = process.memory_info().rss / 1024 / 1024  # MB
        
        # Time the command
        start_time = time.time()
        result = runner.invoke(find_samples, ['-s', str(settings.PIC_SOURCE_PATH_FULL)])
        end_time = time.time()
        
        # Measure memory after
        memory_after = process.memory_info().rss / 1024 / 1024  # MB
        memory_used = memory_after - memory_before
        
        execution_time = end_time - start_time
        
        assert result.exit_code == 0
        
        # Extract photo count from output
        output_lines = result.output.strip().split('\n')
        found_line = next(line for line in output_lines if "Found" in line and "photos" in line)
        photo_count = int(found_line.split()[1])
        
        print("\nPerformance Results:")
        print(f"Photos processed: {photo_count}")
        print(f"Execution time: {execution_time:.2f} seconds")
        print(f"Time per photo: {execution_time/photo_count*1000:.2f} ms")
        print(f"Memory used: {memory_used:.2f} MB")
        
        # Performance assertions - adjust based on expectations
        assert execution_time < 60.0, f"Too slow: {execution_time:.2f}s for {photo_count} photos"
        assert memory_used < 500, f"Too much memory: {memory_used:.2f}MB"
        assert photo_count > 0, "No photos found"
    
    def test_performance_all_filters(self):
        """Test performance with all filter flags"""
        if not settings.PIC_SOURCE_PATH_FULL.exists():
            pytest.skip("No real photos configured")
        
        runner = CliRunner()
        filters = [
            ['--show-bursts'],
            ['--show-conflicts'], 
            ['--show-missing-exif'],
            ['--show-camera-diversity'],
            ['--show-bursts', '--show-conflicts', '--show-missing-exif', '--show-camera-diversity']
        ]
        
        results = {}
        
        for filter_combo in filters:
            filter_name = '+'.join(flag.replace('--show-', '') for flag in filter_combo)
            
            start_time = time.time()
            result = runner.invoke(find_samples, ['-s', str(settings.PIC_SOURCE_PATH_FULL)] + filter_combo)
            end_time = time.time()
            
            assert result.exit_code == 0
            execution_time = end_time - start_time
            results[filter_name] = execution_time
            
            print(f"{filter_name}: {execution_time:.2f}s")
        
        # All filters combined should not be dramatically slower than individual ones
        combined_time = results.get('bursts+conflicts+missing-exif+camera-diversity', 0)
        max_individual = max(results[k] for k in results if '+' not in k)
        
        assert combined_time < max_individual * 3, "Combined filters too slow compared to individual"
    
    def test_large_collection_performance(self):
        """Test with large photo collections (1000+ photos)"""
        if not settings.PIC_SOURCE_PATH_FULL.exists():
            pytest.skip("No real photos configured")
        
        runner = CliRunner()
        
        # Count photos first
        result = runner.invoke(find_samples, ['-s', str(settings.PIC_SOURCE_PATH_FULL)])
        assert result.exit_code == 0
        
        output_lines = result.output.strip().split('\n')
        found_line = next(line for line in output_lines if "Found" in line and "photos" in line)
        photo_count = int(found_line.split()[1])
        
        if photo_count < 1000:
            pytest.skip(f"Not enough photos for large collection test: {photo_count} < 1000")
        
        # Test performance with large collection
        start_time = time.time()
        result = runner.invoke(find_samples, ['-s', str(settings.PIC_SOURCE_PATH_FULL), '--show-camera-diversity'])
        end_time = time.time()
        
        execution_time = end_time - start_time
        time_per_photo = execution_time / photo_count * 1000  # ms per photo
        
        print("\nLarge Collection Performance:")
        print(f"Photos: {photo_count}")
        print(f"Total time: {execution_time:.2f}s")
        print(f"Time per photo: {time_per_photo:.2f}ms")
        
        # Should process at least 10 photos per second
        assert time_per_photo < 100, f"Too slow: {time_per_photo:.2f}ms per photo"