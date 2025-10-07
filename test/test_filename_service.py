"""Tests for filename generation service."""

from datetime import datetime
from pathlib import Path

from src.services.filename_service import (
    generate_photo_filename,
    get_timezone_from_gps, 
    format_iso_timestamp,
    get_camera_code
)
from src.models.photo import ProcessedPhoto, CameraInfo, ExifData


class TestFilenameGeneration:
    """Test core filename generation functionality."""
    
    def test_generate_basic_filename(self):
        """Test basic filename generation with complete metadata."""
        # Create test photo with GPS and timestamp
        camera = CameraInfo(make="Canon", model="EOS R5")
        exif = ExifData(
            timestamp=datetime(2024, 10, 5, 14, 30, 45, 123000),
            subsecond=123,
            gps_latitude=40.7589,  # NYC coordinates
            gps_longitude=-73.9851,
            raw_data={}
        )
        photo = ProcessedPhoto(
            path=Path("test.jpg"),
            filename="test.jpg", 
            file_size=1000,
            camera=camera,
            exif=exif,
            edge_cases=[],
            collection="wedding"
        )
        
        filename = generate_photo_filename(photo, "reception")
        
        # Should use photo's collection ("wedding") over parameter ("reception")
        assert filename.startswith("wedding-")
        assert "20241005T143045.123" in filename
        assert "r5a-001.jpg" in filename
        
    def test_generate_filename_without_gps(self):
        """Test filename generation without GPS coordinates."""
        camera = CameraInfo(make="iPhone", model="15 Pro")
        exif = ExifData(
            timestamp=datetime(2024, 10, 5, 14, 30, 45),
            subsecond=None,
            gps_latitude=None,
            gps_longitude=None,
            raw_data={}
        )
        photo = ProcessedPhoto(
            path=Path("IMG_001.heic"),
            filename="IMG_001.heic",
            file_size=2000,
            camera=camera,
            exif=exif,
            edge_cases=[]
        )
        
        filename = generate_photo_filename(photo, "getting-ready")
        
        assert filename.startswith("getting-ready-")
        assert "20241005T143045.000" in filename
        assert "i15-001.heic" in filename
        
    def test_generate_filename_no_timestamp(self):
        """Test filename generation with missing timestamp (uses current time)."""
        camera = CameraInfo(make="Sony", model="A7R V")
        exif = ExifData(
            timestamp=None,
            subsecond=None,
            gps_latitude=None,
            gps_longitude=None,
            raw_data={}
        )
        photo = ProcessedPhoto(
            path=Path("DSC_001.jpg"),
            filename="DSC_001.jpg",
            file_size=3000,
            camera=camera,
            exif=exif,
            edge_cases=["missing_timestamp"]
        )
        
        filename = generate_photo_filename(photo, "ceremony")
        
        assert filename.startswith("ceremony-")
        # Should contain current year (test will work for several years)
        assert "202" in filename
        assert "a7r-001.jpg" in filename


class TestTimezoneFromGPS:
    """Test GPS to timezone conversion."""
    
    def test_nyc_timezone_standard(self):
        """Test New York timezone in standard time."""
        # January date (standard time)
        timestamp = datetime(2024, 1, 15, 14, 30, 45)
        offset = get_timezone_from_gps(40.7589, -73.9851, timestamp)
        
        assert offset == "-0500"  # EST is UTC-5
        
    def test_nyc_timezone_daylight(self):
        """Test New York timezone in daylight time."""
        # July date (daylight time)
        timestamp = datetime(2024, 7, 15, 14, 30, 45)
        offset = get_timezone_from_gps(40.7589, -73.9851, timestamp)
        
        assert offset == "-0400"  # EDT is UTC-4
        
    def test_london_timezone(self):
        """Test London timezone."""
        # July date (British Summer Time)
        timestamp = datetime(2024, 7, 15, 14, 30, 45)
        offset = get_timezone_from_gps(51.5074, -0.1278, timestamp)
        
        assert offset == "+0100"  # BST is UTC+1
        
    def test_tokyo_timezone(self):
        """Test Tokyo timezone (no DST)."""
        timestamp = datetime(2024, 7, 15, 14, 30, 45)
        offset = get_timezone_from_gps(35.6762, 139.6503, timestamp)
        
        assert offset == "+0900"  # JST is UTC+9
        
    def test_invalid_coordinates_fallback(self):
        """Test fallback to UTC for invalid coordinates."""
        timestamp = datetime(2024, 7, 15, 14, 30, 45)
        offset = get_timezone_from_gps(999.0, 999.0, timestamp)
        
        assert offset == "0000"  # Fallback to UTC


class TestISOTimestampFormatting:
    """Test ISO 8601 timestamp formatting."""
    
    def test_format_basic_timestamp(self):
        """Test basic timestamp formatting."""
        dt = datetime(2024, 10, 5, 14, 30, 45, 123000)
        formatted = format_iso_timestamp(dt, "0400")
        
        assert formatted == "20241005T143045.123Z0400"
        
    def test_format_with_negative_timezone(self):
        """Test formatting with negative timezone offset."""
        dt = datetime(2024, 1, 15, 9, 15, 30, 456000)
        formatted = format_iso_timestamp(dt, "-0500")
        
        assert formatted == "20240115T091530.456Z-0500"
        
    def test_format_zero_milliseconds(self):
        """Test formatting with zero milliseconds."""
        dt = datetime(2024, 12, 25, 23, 59, 59, 0)
        formatted = format_iso_timestamp(dt, "+1030")
        
        assert formatted == "20241225T235959.000Z+1030"
        
    def test_format_microseconds_rounding(self):
        """Test that microseconds are properly converted to milliseconds."""
        dt = datetime(2024, 6, 1, 12, 0, 0, 999999)  # 999 ms + 999 us
        formatted = format_iso_timestamp(dt, "0000")
        
        assert formatted == "20240601T120000.999Z0000"


class TestCameraCodeGeneration:
    """Test camera code extraction."""
    
    def test_canon_r5_mapping(self):
        """Test Canon R5 gets mapped to r5a."""
        camera = CameraInfo(make="Canon", model="EOS R5")
        code = get_camera_code(camera)
        
        assert code == "r5a"
        
    def test_canon_r6_mapping(self):
        """Test Canon R6 gets mapped to r6a."""
        camera = CameraInfo(make="Canon", model="EOS R6")
        code = get_camera_code(camera)
        
        assert code == "r6a"
        
    def test_iphone_mapping(self):
        """Test iPhone gets mapped to iph."""
        camera = CameraInfo(make="Apple", model="iPhone")
        code = get_camera_code(camera)
        
        assert code == "iph"
        
    def test_iphone_15_specific(self):
        """Test iPhone 15 gets specific mapping."""
        camera = CameraInfo(make="Apple", model="iPhone 15")
        code = get_camera_code(camera)
        
        assert code == "i15"
        
    def test_sony_a7r_mapping(self):
        """Test Sony A7R gets mapped to a7r."""
        camera = CameraInfo(make="Sony", model="A7R V")
        code = get_camera_code(camera)
        
        assert code == "a7r"
        
    def test_nikon_d850_mapping(self):
        """Test Nikon D850 gets mapped to d85."""
        camera = CameraInfo(make="Nikon", model="D850")
        code = get_camera_code(camera)
        
        assert code == "d85"
        
    def test_unknown_camera_fallback(self):
        """Test unknown camera falls back to first 3 chars."""
        camera = CameraInfo(make="Unknown", model="TestCam")
        code = get_camera_code(camera)
        
        assert code == "unk"  # "unknowntestcam"[:3]
        
    def test_empty_camera_info(self):
        """Test empty camera info returns 'unk'."""
        camera = CameraInfo(make=None, model=None)
        code = get_camera_code(camera)
        
        assert code == "unk"
        
    def test_only_make_provided(self):
        """Test camera with only make provided."""
        camera = CameraInfo(make="Fujifilm", model=None)
        code = get_camera_code(camera)
        
        assert code == "fuj"  # "fujifilm"[:3]
        
    def test_only_model_provided(self):
        """Test camera with only model provided."""
        camera = CameraInfo(make=None, model="X-T4")
        code = get_camera_code(camera)
        
        assert code == "xt4"  # "x-t4" -> "xt4"
        
    def test_short_name_padding(self):
        """Test short camera names get padded."""
        camera = CameraInfo(make="GH", model="6")
        code = get_camera_code(camera)
        
        assert len(code) == 3
        assert code == "gh6"  # "gh6"


class TestIntegration:
    """Test integration scenarios."""
    
    def test_wedding_collection_canon_r5_nyc(self):
        """Test complete wedding photo from Canon R5 in NYC."""
        camera = CameraInfo(make="Canon", model="EOS R5")
        exif = ExifData(
            timestamp=datetime(2024, 6, 15, 16, 30, 0, 500000),  # 4:30 PM
            subsecond=500,
            gps_latitude=40.7829,  # Central Park
            gps_longitude=-73.9654,
            raw_data={}
        )
        photo = ProcessedPhoto(
            path=Path("IMG_5642.jpg"),
            filename="IMG_5642.jpg",
            file_size=8500000,  # 8.5MB
            camera=camera,
            exif=exif,
            edge_cases=[],
            collection="wedding"
        )
        
        filename = generate_photo_filename(photo)
        
        # Should be summer (EDT = UTC-4)
        expected_parts = [
            "wedding-",
            "20240615T163000.500Z-0400",
            "-r5a-001.jpg"
        ]
        
        for part in expected_parts:
            assert part in filename
            
    def test_burst_sequence_handling_placeholder(self):
        """Test that burst sequences get same timestamp but need different seq numbers."""
        # For now, all photos get seq 001, but this test documents the need
        # for burst sequence handling in the future
        
        camera = CameraInfo(make="Canon", model="EOS R5")
        exif_base = ExifData(
            timestamp=datetime(2024, 10, 5, 14, 30, 45, 123000),
            subsecond=123,
            gps_latitude=40.7589,
            gps_longitude=-73.9851,
            raw_data={}
        )
        
        photos = []
        for i in range(3):
            photo = ProcessedPhoto(
                path=Path(f"IMG_{5000+i}.jpg"),
                filename=f"IMG_{5000+i}.jpg",
                file_size=7000000,
                camera=camera,
                exif=exif_base,
                edge_cases=["burst"],
                collection="ceremony"
            )
            photos.append(photo)
        
        filenames = [generate_photo_filename(photo) for photo in photos]
        
        # Currently all get 001 - this shows we need burst sequence logic
        for filename in filenames:
            assert "-001.jpg" in filename
            
        # TODO: Implement burst sequence numbering
        # Expected behavior:
        # filenames[0] should end with "-001.jpg"
        # filenames[1] should end with "-002.jpg" 
        # filenames[2] should end with "-003.jpg"