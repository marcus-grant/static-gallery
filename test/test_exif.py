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

