import pytest
from datetime import datetime
from pathlib import Path
from PIL import Image
import piexif
from src.services import exif


@pytest.fixture
def create_photo_with_exif(tmp_path):
    """Factory fixture to create test images with custom EXIF data"""

    def _create_photo(filename="test_photo.jpg", **exif_tags):
        img = Image.new("RGB", (32, 32), color="red")

        # Build EXIF dict from kwargs
        exif_dict = {
            "0th": {},
            "Exif": {},
            "1st": {},
            "GPS": {},
        }

        # Add tags based on kwargs
        for tag_name, value in exif_tags.items():
            if tag_name == "DateTimeOriginal":
                exif_dict["Exif"][piexif.ExifIFD.DateTimeOriginal] = (
                    value.encode() if isinstance(value, str) else value
                )
            elif tag_name == "SubSecTimeOriginal":
                exif_dict["Exif"][piexif.ExifIFD.SubSecTimeOriginal] = (
                    value.encode() if isinstance(value, str) else value
                )
            elif tag_name == "Make":
                exif_dict["0th"][piexif.ImageIFD.Make] = (
                    value.encode() if isinstance(value, str) else value
                )
            elif tag_name == "Model":
                exif_dict["0th"][piexif.ImageIFD.Model] = (
                    value.encode() if isinstance(value, str) else value
                )
            # Add more tag mappings as needed

        # Only create EXIF if tags were provided
        photo_path = tmp_path / filename
        if exif_tags:
            exif_bytes = piexif.dump(exif_dict)
            img.save(photo_path, "JPEG", exif=exif_bytes)
        else:
            img.save(photo_path, "JPEG")

        return photo_path

    return _create_photo


class TestGetDatetimeTaken:
    def test_returns_datetime_for_valid_photo(self, create_photo_with_exif):
        """Test returns a datetime object for a photo with EXIF"""
        photo_path = create_photo_with_exif(DateTimeOriginal="2023:09:15 14:30:45")
        result = exif.get_datetime_taken(photo_path)
        assert result == datetime(2023, 9, 15, 14, 30, 45)

    def test_returns_none_for_missing_exif(self, create_photo_with_exif):
        """Test returns None when no EXIF data"""
        photo_path = create_photo_with_exif()  # No EXIF tags
        result = exif.get_datetime_taken(photo_path)
        assert result is None


class TestGetSubsecondPrecision:
    def test_returns_integer_for_valid_subsecond(self, create_photo_with_exif):
        """Test returns integer milliseconds for valid SubSecTimeOriginal"""
        photo_path = create_photo_with_exif(SubSecTimeOriginal="123")
        result = exif.get_subsecond_precision(photo_path)
        assert result == 123


class TestGetCameraInfo:
    def test_returns_make_and_model(self, create_photo_with_exif):
        """Test returns camera make and model when both present"""
        photo_path = create_photo_with_exif(Make="Canon", Model="EOS 5D Mark IV")
        result = exif.get_camera_info(photo_path)
        assert result == {"make": "Canon", "model": "EOS 5D Mark IV"}
    
    def test_returns_none_for_missing_camera_info(self, create_photo_with_exif):
        """Test returns None values when no camera info in EXIF"""
        photo_path = create_photo_with_exif()  # No camera info
        result = exif.get_camera_info(photo_path)
        assert result == {"make": None, "model": None}


class TestExtractExifData:
    def test_returns_dict_with_exif_tags(self, create_photo_with_exif):
        """Test returns dictionary containing all EXIF tags"""
        photo_path = create_photo_with_exif(
            DateTimeOriginal="2023:09:15 14:30:45",
            SubSecTimeOriginal="123",
            Make="Canon",
            Model="EOS 5D Mark IV"
        )
        result = exif.extract_exif_data(photo_path)
        assert isinstance(result, dict)
        assert "EXIF DateTimeOriginal" in result
        assert "EXIF SubSecTimeOriginal" in result
        assert "Image Make" in result
        assert "Image Model" in result
    
    def test_returns_empty_dict_for_no_exif(self, create_photo_with_exif):
        """Test returns empty dict when no EXIF data"""
        photo_path = create_photo_with_exif()  # No EXIF tags
        result = exif.extract_exif_data(photo_path)
        assert result == {}


class TestCombineDatetimeSubsecond:
    def test_adds_subsecond_precision_to_datetime(self):
        """Test combines datetime with subsecond precision"""
        dt = datetime(2023, 9, 15, 14, 30, 45)
        subsec = 123
        result = exif.combine_datetime_subsecond(dt, subsec)
        # Should add 123 milliseconds
        assert result == datetime(2023, 9, 15, 14, 30, 45, 123000)
    
    def test_handles_none_subsecond(self):
        """Test returns original datetime when subsecond is None"""
        dt = datetime(2023, 9, 15, 14, 30, 45)
        result = exif.combine_datetime_subsecond(dt, None)
        assert result == dt
    
    def test_handles_string_subsecond(self):
        """Test handles subsecond as string (from EXIF)"""
        dt = datetime(2023, 9, 15, 14, 30, 45)
        result = exif.combine_datetime_subsecond(dt, "456")
        assert result == datetime(2023, 9, 15, 14, 30, 45, 456000)
    
    def test_handles_two_digit_subsecond(self):
        """Test handles two-digit subsecond (10ms precision)"""
        dt = datetime(2023, 9, 15, 14, 30, 45)
        result = exif.combine_datetime_subsecond(dt, "12")
        # "12" should be interpreted as 120ms (0.12 seconds)
        assert result == datetime(2023, 9, 15, 14, 30, 45, 120000)
    
    def test_handles_one_digit_subsecond(self):
        """Test handles single-digit subsecond (100ms precision)"""
        dt = datetime(2023, 9, 15, 14, 30, 45)
        result = exif.combine_datetime_subsecond(dt, "5")
        # "5" should be interpreted as 500ms (0.5 seconds)
        assert result == datetime(2023, 9, 15, 14, 30, 45, 500000)


class TestHasSubsecondPrecision:
    def test_returns_true_for_photo_with_subsecond(self, create_photo_with_exif):
        """Test returns True when SubSecTimeOriginal present"""
        photo_path = create_photo_with_exif(SubSecTimeOriginal="123")
        result = exif.has_subsecond_precision(photo_path)
        assert result is True
    
    def test_returns_false_for_photo_without_subsecond(self, create_photo_with_exif):
        """Test returns False when no SubSecTimeOriginal"""
        photo_path = create_photo_with_exif(DateTimeOriginal="2023:09:15 14:30:45")
        result = exif.has_subsecond_precision(photo_path)
        assert result is False
    
    def test_handles_nonexistent_file(self):
        """Test returns False for nonexistent file"""
        result = exif.has_subsecond_precision("/nonexistent/photo.jpg")
        assert result is False


class TestSortPhotosChronologically:
    def test_sorts_photos_by_timestamp(self, create_photo_with_exif):
        """Test sorts photos by their EXIF timestamps"""
        # Create photos with different timestamps
        photo1 = create_photo_with_exif(
            "photo1.jpg", 
            DateTimeOriginal="2023:09:15 14:30:45"
        )
        photo2 = create_photo_with_exif(
            "photo2.jpg",
            DateTimeOriginal="2023:09:15 14:30:30"  # Earlier
        )
        photo3 = create_photo_with_exif(
            "photo3.jpg",
            DateTimeOriginal="2023:09:15 14:31:00"  # Later
        )
        
        result = exif.sort_photos_chronologically([photo1, photo2, photo3])
        
        # Should be sorted by timestamp
        assert len(result) == 3
        assert result[0][0] == photo2  # Earliest
        assert result[1][0] == photo1  # Middle
        assert result[2][0] == photo3  # Latest
        assert result[0][1] == datetime(2023, 9, 15, 14, 30, 30)
        assert result[1][1] == datetime(2023, 9, 15, 14, 30, 45)
        assert result[2][1] == datetime(2023, 9, 15, 14, 31, 0)
        # Check camera info is included
        assert isinstance(result[0][2], dict)
        assert isinstance(result[1][2], dict)
        assert isinstance(result[2][2], dict)
    
    def test_camera_then_filename_fallback_for_identical_timestamps(self, create_photo_with_exif):
        """Test uses camera then filename for sorting when timestamps are identical"""
        # Create photos with same timestamp but different cameras
        photo_a = create_photo_with_exif(
            "IMG_003.jpg",
            DateTimeOriginal="2023:09:15 14:30:45",
            Make="Canon",
            Model="EOS 5D"
        )
        photo_b = create_photo_with_exif(
            "IMG_001.jpg",
            DateTimeOriginal="2023:09:15 14:30:45",
            Make="Nikon",
            Model="D850"
        )
        photo_c = create_photo_with_exif(
            "IMG_002.jpg",
            DateTimeOriginal="2023:09:15 14:30:45",
            Make="Canon",
            Model="EOS 5D"
        )
        
        result = exif.sort_photos_chronologically([photo_a, photo_b, photo_c])
        
        # Should be sorted by camera (Canon before Nikon), then filename
        assert len(result) == 3
        assert result[0][0] == photo_c  # Canon IMG_002
        assert result[1][0] == photo_a  # Canon IMG_003
        assert result[2][0] == photo_b  # Nikon IMG_001
        # Verify camera info
        assert result[0][2]["make"] == "Canon"
        assert result[2][2]["make"] == "Nikon"
    
    def test_sorts_with_subsecond_precision(self, create_photo_with_exif):
        """Test incorporates subsecond precision for accurate burst sorting"""
        # Create photos with same second but different subseconds
        photo1 = create_photo_with_exif(
            "burst_002.jpg",
            DateTimeOriginal="2023:09:15 14:30:45",
            SubSecTimeOriginal="200"  # 200ms
        )
        photo2 = create_photo_with_exif(
            "burst_001.jpg",
            DateTimeOriginal="2023:09:15 14:30:45",
            SubSecTimeOriginal="100"  # 100ms - should be first
        )
        photo3 = create_photo_with_exif(
            "burst_003.jpg",
            DateTimeOriginal="2023:09:15 14:30:45",
            SubSecTimeOriginal="300"  # 300ms
        )
        
        result = exif.sort_photos_chronologically([photo1, photo2, photo3])
        
        # Should be sorted by subsecond precision
        assert len(result) == 3
        assert result[0][0] == photo2  # 100ms
        assert result[1][0] == photo1  # 200ms
        assert result[2][0] == photo3  # 300ms
        # Check timestamps include subseconds
        assert result[0][1] == datetime(2023, 9, 15, 14, 30, 45, 100000)
        assert result[1][1] == datetime(2023, 9, 15, 14, 30, 45, 200000)
        assert result[2][1] == datetime(2023, 9, 15, 14, 30, 45, 300000)


class TestIsBurstCandidate:
    def test_returns_true_for_photos_within_burst_interval(self, create_photo_with_exif):
        """Test identifies photos taken within burst interval"""
        photo1 = create_photo_with_exif(
            "burst1.jpg",
            DateTimeOriginal="2023:09:15 14:30:45",
            SubSecTimeOriginal="100"
        )
        photo2 = create_photo_with_exif(
            "burst2.jpg", 
            DateTimeOriginal="2023:09:15 14:30:45",
            SubSecTimeOriginal="250"  # 150ms later
        )
        
        result = exif.is_burst_candidate(photo1, photo2, max_interval_ms=200)
        assert result is True
    
    def test_returns_false_for_photos_outside_burst_interval(self, create_photo_with_exif):
        """Test returns False when photos are too far apart"""
        photo1 = create_photo_with_exif(
            "photo1.jpg",
            DateTimeOriginal="2023:09:15 14:30:45",
            SubSecTimeOriginal="100"
        )
        photo2 = create_photo_with_exif(
            "photo2.jpg",
            DateTimeOriginal="2023:09:15 14:30:45",
            SubSecTimeOriginal="400"  # 300ms later
        )
        
        result = exif.is_burst_candidate(photo1, photo2, max_interval_ms=200)
        assert result is False
    
    def test_returns_false_for_missing_timestamps(self, create_photo_with_exif):
        """Test returns False when photos lack EXIF timestamps"""
        photo1 = create_photo_with_exif("photo1.jpg")  # No EXIF
        photo2 = create_photo_with_exif(
            "photo2.jpg",
            DateTimeOriginal="2023:09:15 14:30:45"
        )
        
        result = exif.is_burst_candidate(photo1, photo2)
        assert result is False


class TestDetectBurstSequences:
    def test_groups_photos_in_burst_sequences(self, create_photo_with_exif):
        """Test groups consecutive photos within burst interval"""
        # Create a burst sequence
        photo1 = create_photo_with_exif(
            "burst1.jpg",
            DateTimeOriginal="2023:09:15 14:30:45",
            SubSecTimeOriginal="100"
        )
        photo2 = create_photo_with_exif(
            "burst2.jpg",
            DateTimeOriginal="2023:09:15 14:30:45", 
            SubSecTimeOriginal="200"  # 100ms later
        )
        photo3 = create_photo_with_exif(
            "burst3.jpg",
            DateTimeOriginal="2023:09:15 14:30:45",
            SubSecTimeOriginal="300"  # 100ms later
        )
        # Photo outside burst window
        photo4 = create_photo_with_exif(
            "single.jpg",
            DateTimeOriginal="2023:09:15 14:30:46"  # 1 second later
        )
        
        # Sort photos first (as per the function signature)
        sorted_photos = exif.sort_photos_chronologically([photo1, photo2, photo3, photo4])
        
        # Detect burst sequences
        result = exif.detect_burst_sequences(sorted_photos)
        
        # Should have 1 burst sequence with 3 photos
        assert len(result) == 1
        assert len(result[0]) == 3
        assert photo1 in result[0]
        assert photo2 in result[0]
        assert photo3 in result[0]
    
    def test_detects_multiple_burst_sequences(self, create_photo_with_exif):
        """Test identifies multiple separate burst sequences"""
        # First burst
        burst1_1 = create_photo_with_exif(
            "burst1_1.jpg",
            DateTimeOriginal="2023:09:15 14:30:45",
            SubSecTimeOriginal="100"
        )
        burst1_2 = create_photo_with_exif(
            "burst1_2.jpg",
            DateTimeOriginal="2023:09:15 14:30:45",
            SubSecTimeOriginal="200"
        )
        
        # Gap
        single = create_photo_with_exif(
            "single.jpg",
            DateTimeOriginal="2023:09:15 14:30:46"
        )
        
        # Second burst
        burst2_1 = create_photo_with_exif(
            "burst2_1.jpg",
            DateTimeOriginal="2023:09:15 14:30:47",
            SubSecTimeOriginal="100"
        )
        burst2_2 = create_photo_with_exif(
            "burst2_2.jpg",
            DateTimeOriginal="2023:09:15 14:30:47",
            SubSecTimeOriginal="200"
        )
        
        sorted_photos = exif.sort_photos_chronologically(
            [burst1_1, burst1_2, single, burst2_1, burst2_2]
        )
        result = exif.detect_burst_sequences(sorted_photos)
        
        # Should have 2 burst sequences
        assert len(result) == 2
        assert len(result[0]) == 2  # First burst
        assert len(result[1]) == 2  # Second burst
        assert burst1_1 in result[0]
        assert burst1_2 in result[0]
        assert burst2_1 in result[1]
        assert burst2_2 in result[1]


class TestFindTimestampConflicts:
    def test_finds_photos_with_same_timestamp_different_cameras(self, create_photo_with_exif):
        """Test identifies photos taken at same time by different cameras"""
        # Same timestamp, different cameras
        canon1 = create_photo_with_exif(
            "canon1.jpg",
            DateTimeOriginal="2023:09:15 14:30:45",
            Make="Canon",
            Model="EOS 5D"
        )
        nikon1 = create_photo_with_exif(
            "nikon1.jpg",
            DateTimeOriginal="2023:09:15 14:30:45",
            Make="Nikon",
            Model="D850"
        )
        canon2 = create_photo_with_exif(
            "canon2.jpg",
            DateTimeOriginal="2023:09:15 14:30:45",
            Make="Canon",
            Model="EOS R5"  # Different Canon model
        )
        # Different timestamp
        other = create_photo_with_exif(
            "other.jpg",
            DateTimeOriginal="2023:09:15 14:30:46"
        )
        
        result = exif.find_timestamp_conflicts([canon1, nikon1, canon2, other])
        
        # Should have one conflict group with 3 photos
        assert len(result) == 1
        assert len(result[0]) == 3
        assert canon1 in result[0]
        assert nikon1 in result[0]
        assert canon2 in result[0]
        assert other not in result[0]


class TestFindMissingExifPhotos:
    def test_identifies_photos_without_exif_data(self, create_photo_with_exif):
        """Test finds photos missing critical EXIF data"""
        # Photo with complete EXIF
        complete = create_photo_with_exif(
            "complete.jpg",
            DateTimeOriginal="2023:09:15 14:30:45",
            Make="Canon",
            Model="EOS 5D"
        )
        # Photo without any EXIF
        no_exif = create_photo_with_exif("no_exif.jpg")
        # Photo with partial EXIF (no timestamp)
        no_timestamp = create_photo_with_exif(
            "no_timestamp.jpg",
            Make="Canon",
            Model="EOS 5D"
        )
        
        result = exif.find_missing_exif_photos([complete, no_exif, no_timestamp])
        
        # Should identify both photos without timestamps
        assert len(result) == 2
        assert no_exif in result
        assert no_timestamp in result
        assert complete not in result


class TestGetCameraDiversitySamples:
    def test_groups_photos_by_camera_make_model(self, create_photo_with_exif):
        """Test groups photos by camera make/model"""
        # Canon 5D photos
        canon5d_1 = create_photo_with_exif(
            "canon5d_1.jpg",
            DateTimeOriginal="2023:09:15 14:30:45",
            Make="Canon",
            Model="EOS 5D Mark IV"
        )
        canon5d_2 = create_photo_with_exif(
            "canon5d_2.jpg",
            DateTimeOriginal="2023:09:15 14:30:46",
            Make="Canon",
            Model="EOS 5D Mark IV"
        )
        # Nikon D850
        nikon = create_photo_with_exif(
            "nikon.jpg",
            DateTimeOriginal="2023:09:15 14:30:45",
            Make="Nikon",
            Model="D850"
        )
        # iPhone
        iphone = create_photo_with_exif(
            "iphone.jpg",
            DateTimeOriginal="2023:09:15 14:30:45",
            Make="Apple",
            Model="iPhone 13 Pro"
        )
        # No camera info
        no_camera = create_photo_with_exif(
            "no_camera.jpg",
            DateTimeOriginal="2023:09:15 14:30:45"
        )
        
        result = exif.get_camera_diversity_samples(
            [canon5d_1, canon5d_2, nikon, iphone, no_camera]
        )
        
        # Should have groups for each camera
        assert len(result) == 4  # 3 cameras + 1 unknown
        
        # Check Canon group
        canon_key = ("Canon", "EOS 5D Mark IV")
        assert canon_key in result
        assert len(result[canon_key]) == 2
        assert canon5d_1 in result[canon_key]
        assert canon5d_2 in result[canon_key]
        
        # Check other cameras
        assert ("Nikon", "D850") in result
        assert ("Apple", "iPhone 13 Pro") in result
        assert (None, None) in result  # Unknown camera group

