import pytest
from click.testing import CliRunner
from pathlib import Path
from PIL import Image
import piexif
from src.command.find_samples import find_samples


@pytest.fixture
def create_edge_case_photos(tmp_path):
    """Creates photos covering all the edge cases"""
    def _create():
        photos = []
        
        def create_photo(filename, **exif_tags):
            img = Image.new("RGB", (100, 100), color="red")
            photo_path = tmp_path / filename
            
            if exif_tags:
                exif_dict = {"0th": {}, "Exif": {}, "1st": {}, "GPS": {}}
                
                if "DateTimeOriginal" in exif_tags:
                    exif_dict["Exif"][piexif.ExifIFD.DateTimeOriginal] = exif_tags["DateTimeOriginal"].encode()
                if "SubSecTimeOriginal" in exif_tags:
                    exif_dict["Exif"][piexif.ExifIFD.SubSecTimeOriginal] = exif_tags["SubSecTimeOriginal"].encode()
                if "Make" in exif_tags:
                    exif_dict["0th"][piexif.ImageIFD.Make] = exif_tags["Make"].encode()
                if "Model" in exif_tags:
                    exif_dict["0th"][piexif.ImageIFD.Model] = exif_tags["Model"].encode()
                
                exif_bytes = piexif.dump(exif_dict)
                img.save(photo_path, "JPEG", exif=exif_bytes)
            else:
                img.save(photo_path, "JPEG")
                
            photos.append(photo_path)
            return photo_path
        
        # 1. BURST SEQUENCES - same timestamp, subsecond precision
        create_photo("burst_001.jpg", 
                    DateTimeOriginal="2023:09:15 14:30:45",
                    SubSecTimeOriginal="100",
                    Make="Canon", Model="EOS R5")
        create_photo("burst_002.jpg",
                    DateTimeOriginal="2023:09:15 14:30:45",
                    SubSecTimeOriginal="200",
                    Make="Canon", Model="EOS R5")
        create_photo("burst_003.jpg",
                    DateTimeOriginal="2023:09:15 14:30:45", 
                    SubSecTimeOriginal="300",
                    Make="Canon", Model="EOS R5")
        
        # 2. SAME TIMESTAMP, DIFFERENT CAMERAS (multi-photographer)
        create_photo("wedding_canon.jpg",
                    DateTimeOriginal="2023:09:15 15:00:00",
                    Make="Canon", Model="EOS 5D Mark IV")
        create_photo("wedding_nikon.jpg",
                    DateTimeOriginal="2023:09:15 15:00:00",
                    Make="Nikon", Model="D850")
        create_photo("wedding_sony.jpg",
                    DateTimeOriginal="2023:09:15 15:00:00",
                    Make="Sony", Model="A7R IV")
        
        # 3. SAME TIMESTAMP, SAME CAMERA - filename fallback needed
        create_photo("IMG_100.jpg",
                    DateTimeOriginal="2023:09:15 16:00:00",
                    Make="Canon", Model="EOS 5D")
        create_photo("IMG_200.jpg",
                    DateTimeOriginal="2023:09:15 16:00:00",
                    Make="Canon", Model="EOS 5D")
        create_photo("IMG_050.jpg",  # Should sort first by filename
                    DateTimeOriginal="2023:09:15 16:00:00",
                    Make="Canon", Model="EOS 5D")
        
        # 4. NO EXIF - filesystem metadata fallback
        create_photo("no_exif_a.jpg")
        create_photo("no_exif_b.jpg")
        create_photo("no_exif_c.jpg")
        
        # 5. PARTIAL EXIF - camera but no timestamp
        create_photo("partial_canon.jpg",
                    Make="Canon", Model="EOS 5D")
        create_photo("partial_nikon.jpg",
                    Make="Nikon", Model="D850")
        
        # 6. BURST WITHOUT SUBSECOND (older cameras)
        create_photo("old_burst_1.jpg",
                    DateTimeOriginal="2023:09:15 17:00:00",
                    Make="Canon", Model="EOS 40D")
        create_photo("old_burst_2.jpg",
                    DateTimeOriginal="2023:09:15 17:00:00",
                    Make="Canon", Model="EOS 40D")
        
        return tmp_path, photos
    
    return _create


class TestFindSamplesEdgeCases:
    """E2E tests for edge cases in find-samples command"""
    
    def test_burst_detection_with_subsecond(self, create_edge_case_photos):
        """Test burst detection with subsecond precision"""
        test_dir, photos = create_edge_case_photos()
        runner = CliRunner()
        
        result = runner.invoke(find_samples, ['-s', str(test_dir), '--show-bursts'])
        
        assert result.exit_code == 0
        assert "Found 3 burst sequence(s):" in result.output
        # First burst with subsecond
        assert "burst_001.jpg" in result.output
        assert "burst_002.jpg" in result.output
        assert "burst_003.jpg" in result.output
        # Second burst without subsecond (old cameras)
        assert "old_burst_1.jpg" in result.output
        assert "old_burst_2.jpg" in result.output
    
    def test_timestamp_conflicts_different_cameras(self, create_edge_case_photos):
        """Test detection of same timestamp from different photographers"""
        test_dir, photos = create_edge_case_photos()
        runner = CliRunner()
        
        result = runner.invoke(find_samples, ['-s', str(test_dir), '--show-conflicts'])
        
        assert result.exit_code == 0
        # Should find at least the multi-photographer scenario
        assert "timestamp conflict(s):" in result.output
        assert "Canon EOS 5D Mark IV" in result.output
        assert "Nikon D850" in result.output
        assert "Sony A7R IV" in result.output
    
    def test_sorting_with_filename_fallback(self, create_edge_case_photos):
        """Test that identical timestamp+camera falls back to filename sorting"""
        test_dir, photos = create_edge_case_photos()
        runner = CliRunner()
        
        # Use basic listing to see sort order
        result = runner.invoke(find_samples, ['-s', str(test_dir)])
        
        assert result.exit_code == 0
        # Check that IMG_050 comes before IMG_100 and IMG_200
        output_lines = result.output.split('\n')
        img_lines = [line for line in output_lines if 'IMG_' in line]
        
        # Find positions
        pos_050 = next(i for i, line in enumerate(img_lines) if 'IMG_050.jpg' in line)
        pos_100 = next(i for i, line in enumerate(img_lines) if 'IMG_100.jpg' in line)
        pos_200 = next(i for i, line in enumerate(img_lines) if 'IMG_200.jpg' in line)
        
        assert pos_050 < pos_100 < pos_200, "Files should be sorted by filename when timestamp/camera are identical"
    
    def test_missing_exif_detection(self, create_edge_case_photos):
        """Test detection of photos without timestamps"""
        test_dir, photos = create_edge_case_photos()
        runner = CliRunner()
        
        result = runner.invoke(find_samples, ['-s', str(test_dir), '--show-missing-exif'])
        
        assert result.exit_code == 0
        assert "Found 5 photo(s) without EXIF timestamps:" in result.output
        # No EXIF at all
        assert "no_exif_a.jpg" in result.output
        assert "no_exif_b.jpg" in result.output
        assert "no_exif_c.jpg" in result.output
        # Partial EXIF (camera but no timestamp)
        assert "partial_canon.jpg" in result.output
        assert "partial_nikon.jpg" in result.output
    
    def test_camera_diversity_with_unknowns(self, create_edge_case_photos):
        """Test camera diversity including unknown cameras"""
        test_dir, photos = create_edge_case_photos()
        runner = CliRunner()
        
        result = runner.invoke(find_samples, ['-s', str(test_dir), '--show-camera-diversity'])
        
        assert result.exit_code == 0
        # Should show all cameras including unknown
        assert "Canon EOS R5" in result.output
        assert "Canon EOS 5D Mark IV" in result.output
        assert "Nikon D850" in result.output
        assert "Sony A7R IV" in result.output
        assert "Canon EOS 40D" in result.output
        assert "Unknown camera: 3 photos" in result.output  # The no_exif photos