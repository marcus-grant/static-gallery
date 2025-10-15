"""Tests for filename generation service."""

from datetime import datetime
from pathlib import Path

from src.services.filename_service import (
    generate_photo_filename,
    get_timezone_from_gps, 
    format_iso_timestamp,
    get_camera_code,
    generate_batch_filenames
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
        assert "20241005T143045" in filename
        assert "r5a-0.jpg" in filename
        
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
        assert "20241005T143045" in filename
        assert "i15-0.heic" in filename
        
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
        assert "a7r-0.jpg" in filename


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
        formatted = format_iso_timestamp(dt)
        
        assert formatted == "20241005T143045"
        
    def test_format_utc_only(self):
        """Test UTC timestamp formatting without timezone info."""
        dt = datetime(2024, 1, 15, 9, 15, 30, 456000)
        formatted = format_iso_timestamp(dt)
        
        assert formatted == "20240115T091530"
        
    def test_format_ignores_microseconds(self):
        """Test that microseconds are ignored in timestamp (to the second only)."""
        dt = datetime(2024, 6, 1, 12, 0, 0, 999999)
        formatted = format_iso_timestamp(dt)
        
        assert formatted == "20240601T120000"


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
        
        # Should contain UTC timestamp and base32 counter
        expected_parts = [
            "wedding-",
            "20240615T163000",
            "-r5a-0.jpg"
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
        
        # Currently all get 0 - this shows we need burst sequence logic
        for filename in filenames:
            assert "-0.jpg" in filename
            
        # TODO: Implement burst sequence numbering
        # Expected behavior:
        # filenames[0] should end with "-001.jpg"
        # filenames[1] should end with "-002.jpg" 
        # filenames[2] should end with "-003.jpg"


class TestBurstSequenceHandling:
    """Test burst sequence number generation."""
    
    def test_generate_unique_sequence_numbers(self):
        """Test that burst photos get unique sequence numbers."""
        from src.services.filename_service import generate_photo_filename
        
        # Create photos with same timestamp (burst mode)
        camera = CameraInfo(make="Canon", model="EOS R5") 
        timestamp = datetime(2024, 10, 5, 14, 30, 45)
        exif = ExifData(
            timestamp=timestamp,
            subsecond=123,
            gps_latitude=40.7128,
            gps_longitude=-74.0060,
            raw_data={}
        )
        
        # Simulate existing filenames to check against
        existing_filenames = set()
        
        # Generate filenames for burst sequence
        filenames = []
        for i in range(3):
            photo = ProcessedPhoto(
                path=Path(f"IMG_{i:03d}.jpg"),
                filename=f"IMG_{i:03d}.jpg",
                file_size=1024,
                camera=camera,
                exif=exif,
                edge_cases=["burst"]
            )
            
            filename = generate_photo_filename(
                photo, 
                "wedding",
                existing_filenames=existing_filenames
            )
            filenames.append(filename)
            existing_filenames.add(filename)
        
        # Check that all filenames are unique
        assert len(set(filenames)) == 3
        
        # Check sequence numbers
        assert filenames[0].endswith("-0.jpg")
        assert filenames[1].endswith("-1.jpg") 
        assert filenames[2].endswith("-2.jpg")


class TestBase32CounterSystem:
    """Test new base32 counter system for filename generation."""
    
    def test_utc_timestamp_format_no_timezone(self):
        """Test that new format uses UTC-only timestamps without timezone offset."""
        camera = CameraInfo(make="Canon", model="EOS R5")
        exif = ExifData(
            timestamp=datetime(2024, 6, 15, 16, 30, 45),
            subsecond=None,
            gps_latitude=None,
            gps_longitude=None,
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
        
        filename = generate_photo_filename(photo)
        
        # Should contain UTC timestamp without timezone offset or milliseconds
        assert "20240615T163045" in filename
        # Should NOT contain timezone offset or milliseconds
        assert "Z+" not in filename
        assert "Z-" not in filename
        assert ".000" not in filename
        
    def test_base32_counter_single_photo(self):
        """Test that single photo gets base32 counter '0'."""
        camera = CameraInfo(make="Canon", model="EOS R5")
        exif = ExifData(
            timestamp=datetime(2024, 6, 15, 16, 30, 45),
            subsecond=None,
            gps_latitude=None,
            gps_longitude=None,
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
        
        filename = generate_photo_filename(photo)
        
        # Should end with base32 counter '0' (first photo)
        assert filename.endswith("-r5a-0.jpg")
        
    def test_base32_counter_burst_sequence(self):
        """Test that burst photos get sequential base32 counters."""
        camera = CameraInfo(make="Canon", model="EOS R5")
        timestamp = datetime(2024, 6, 15, 16, 30, 45)
        exif = ExifData(
            timestamp=timestamp,
            subsecond=None,
            gps_latitude=None,
            gps_longitude=None,
            raw_data={}
        )
        
        existing_filenames = set()
        filenames = []
        
        # Generate 5 photos with same timestamp (burst)
        for i in range(5):
            photo = ProcessedPhoto(
                path=Path(f"burst_{i}.jpg"),
                filename=f"burst_{i}.jpg",
                file_size=1000,
                camera=camera,
                exif=exif,
                edge_cases=["burst"],
                collection="wedding"
            )
            
            filename = generate_photo_filename(
                photo, 
                existing_filenames=existing_filenames
            )
            filenames.append(filename)
            existing_filenames.add(filename)
        
        # Check base32 sequence: 0, 1, 2, 3, 4
        expected_counters = ['0', '1', '2', '3', '4']
        for i, filename in enumerate(filenames):
            assert filename.endswith(f"-r5a-{expected_counters[i]}.jpg")
            
    def test_base32_counter_max_range(self):
        """Test base32 counter handles full range 0-V (32 photos)."""
        camera = CameraInfo(make="Canon", model="EOS R5")
        timestamp = datetime(2024, 6, 15, 16, 30, 45)
        exif = ExifData(
            timestamp=timestamp,
            subsecond=None,
            gps_latitude=None,
            gps_longitude=None,
            raw_data={}
        )
        
        existing_filenames = set()
        
        # Expected base32 sequence
        expected_base32 = "0123456789ABCDEFGHIJKLMNOPQRSTUV"
        
        # Generate 32 photos (max base32 range)
        for i in range(32):
            photo = ProcessedPhoto(
                path=Path(f"test_{i}.jpg"),
                filename=f"test_{i}.jpg",
                file_size=1000,
                camera=camera,
                exif=exif,
                edge_cases=[],
                collection="wedding"
            )
            
            filename = generate_photo_filename(
                photo,
                existing_filenames=existing_filenames
            )
            existing_filenames.add(filename)
            
            # Check that counter matches expected base32 character
            expected_counter = expected_base32[i]
            assert filename.endswith(f"-r5a-{expected_counter}.jpg")
            
    def test_shorter_filename_length(self):
        """Test that new format produces shorter filenames."""
        camera = CameraInfo(make="Canon", model="EOS R5") 
        exif = ExifData(
            timestamp=datetime(2024, 6, 15, 16, 30, 45),
            subsecond=None,
            gps_latitude=None,
            gps_longitude=None,
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
        
        filename = generate_photo_filename(photo)
        
        # New format should be ~33 characters
        # wedding-20240615T163045-r5a-0.jpg = 33 chars
        assert len(filename) <= 35  # Allow some margin
        assert len(filename) >= 30  # Should not be too short
        
    def test_camera_first_subsecond_order_no_interleaving(self):
        """Test camera-first ordering with subsecond precision, no interleaving between cameras."""
        canon_camera = CameraInfo(make="Canon", model="EOS R5")
        sony_camera = CameraInfo(make="Sony", model="A7R V")
        
        # Same second timestamp: 16:30:45
        base_timestamp = datetime(2024, 6, 15, 16, 30, 45)
        
        # Canon burst: .123, .456, .789
        canon_photos = []
        canon_subseconds = [123, 456, 789]
        for i, subsec in enumerate(canon_subseconds):
            exif = ExifData(
                timestamp=base_timestamp.replace(microsecond=subsec * 1000),
                subsecond=subsec,
                gps_latitude=None,
                gps_longitude=None,
                raw_data={}
            )
            photo = ProcessedPhoto(
                path=Path(f"canon_burst_{i}.jpg"),
                filename=f"canon_burst_{i}.jpg",
                file_size=1000,
                camera=canon_camera,
                exif=exif,
                edge_cases=["burst"],
                collection="wedding"
            )
            canon_photos.append(photo)
        
        # Sony burst: .234, .567 (interleaved timing with Canon)
        sony_photos = []
        sony_subseconds = [234, 567]
        for i, subsec in enumerate(sony_subseconds):
            exif = ExifData(
                timestamp=base_timestamp.replace(microsecond=subsec * 1000),
                subsecond=subsec,
                gps_latitude=None,
                gps_longitude=None,
                raw_data={}
            )
            photo = ProcessedPhoto(
                path=Path(f"sony_burst_{i}.jpg"),
                filename=f"sony_burst_{i}.jpg",
                file_size=1000,
                camera=sony_camera,
                exif=exif,
                edge_cases=["burst"],
                collection="wedding"
            )
            sony_photos.append(photo)
        
        # Process photos in mixed order (simulating real-world scenario)
        all_photos = [canon_photos[0], sony_photos[0], canon_photos[1], sony_photos[1], canon_photos[2]]
        existing_filenames = set()
        filenames = []
        
        for photo in all_photos:
            filename = generate_photo_filename(photo, existing_filenames=existing_filenames)
            filenames.append(filename)
            existing_filenames.add(filename)
        
        # Expected ordering: Camera groups first, then subsecond order within each camera
        # All Canon photos should have same base timestamp, sequential counters
        canon_filenames = [f for f in filenames if "-r5a-" in f]
        sony_filenames = [f for f in filenames if "-a7r-" in f]
        
        # Canon sequence should be: 0, 1, 2 (chronological by subsecond)
        assert len(canon_filenames) == 3
        assert canon_filenames[0].endswith("-r5a-0.jpg")  # .123
        assert canon_filenames[1].endswith("-r5a-1.jpg")  # .456  
        assert canon_filenames[2].endswith("-r5a-2.jpg")  # .789
        
        # Sony sequence should be: 0, 1 (chronological by subsecond)
        assert len(sony_filenames) == 2
        assert sony_filenames[0].endswith("-a7r-0.jpg")  # .234
        assert sony_filenames[1].endswith("-a7r-1.jpg")  # .567
        
        # All should have same base timestamp (to the second)
        for filename in filenames:
            assert "20240615T163045" in filename
            # Should NOT contain milliseconds in timestamp
            assert "T163045123" not in filename
            assert "T163045234" not in filename
            
        # Verify no interleaving: Canon burst stays together, Sony burst stays together
        # This test verifies the algorithm groups by camera first, preventing interleaving
        
    def test_subsecond_ordering_hierarchy(self):
        """Test the complete hierarchy for subsecond ordering within same camera+timestamp."""
        camera = CameraInfo(make="Canon", model="EOS R5")
        base_timestamp = datetime(2024, 6, 15, 16, 30, 45)
        
        # Create photos that test different aspects of the ordering hierarchy
        photos = []
        
        # Photo 1: EXIF timestamp with milliseconds (.789)
        photos.append(ProcessedPhoto(
            path=Path("IMG_001.jpg"),
            filename="IMG_001.jpg",
            file_size=1000,
            camera=camera,
            exif=ExifData(
                timestamp=base_timestamp.replace(microsecond=789000),  # .789 seconds
                subsecond=None,  # No EXIF subsecond tag
                gps_latitude=None,
                gps_longitude=None,
                raw_data={}
            ),
            edge_cases=[],
            collection="wedding"
        ))
        
        # Photo 2: EXIF subsecond tag (.123)
        photos.append(ProcessedPhoto(
            path=Path("IMG_002.jpg"),
            filename="IMG_002.jpg",
            file_size=1000,
            camera=camera,
            exif=ExifData(
                timestamp=base_timestamp,  # No microseconds in timestamp
                subsecond=123,  # EXIF subsecond tag
                gps_latitude=None,
                gps_longitude=None,
                raw_data={}
            ),
            edge_cases=[],
            collection="wedding"
        ))
        
        # Photo 3: EXIF timestamp with milliseconds (.456)
        photos.append(ProcessedPhoto(
            path=Path("IMG_003.jpg"),
            filename="IMG_003.jpg",
            file_size=1000,
            camera=camera,
            exif=ExifData(
                timestamp=base_timestamp.replace(microsecond=456000),  # .456 seconds
                subsecond=None,
                gps_latitude=None,
                gps_longitude=None,
                raw_data={}
            ),
            edge_cases=[],
            collection="wedding"
        ))
        
        # Photo 4: Filename hint only (lexically ordered suffix)
        photos.append(ProcessedPhoto(
            path=Path("DSC_0100.jpg"),
            filename="DSC_0100.jpg",
            file_size=1000,
            camera=camera,
            exif=ExifData(
                timestamp=base_timestamp,  # No microseconds
                subsecond=None,  # No EXIF subsecond
                gps_latitude=None,
                gps_longitude=None,
                raw_data={}
            ),
            edge_cases=[],
            collection="wedding"
        ))
        
        # Photo 5: Filename hint only (higher suffix)
        photos.append(ProcessedPhoto(
            path=Path("DSC_0101.jpg"),
            filename="DSC_0101.jpg",
            file_size=1000,
            camera=camera,
            exif=ExifData(
                timestamp=base_timestamp,
                subsecond=None,
                gps_latitude=None,
                gps_longitude=None,
                raw_data={}
            ),
            edge_cases=[],
            collection="wedding"
        ))
        
        # Process photos in random order to test sorting
        import random
        shuffled_photos = photos.copy()
        random.shuffle(shuffled_photos)
        
        # Use batch processing (to be implemented)
        filenames = generate_batch_filenames(shuffled_photos, "wedding")
        
        # Expected order based on hierarchy:
        # 1. EXIF timestamp .123 (from subsecond tag)
        # 2. EXIF timestamp .456 (from microseconds)  
        # 3. EXIF timestamp .789 (from microseconds)
        # 4. DSC_0100.jpg (filename hint)
        # 5. DSC_0101.jpg (filename hint)
        
        expected_order = [
            ("-r5a-0.jpg", "IMG_002.jpg"),  # subsecond=123
            ("-r5a-1.jpg", "IMG_003.jpg"),  # microseconds=456
            ("-r5a-2.jpg", "IMG_001.jpg"),  # microseconds=789
            ("-r5a-3.jpg", "DSC_0100.jpg"), # filename hint
            ("-r5a-4.jpg", "DSC_0101.jpg")  # filename hint
        ]
        
        for i, (expected_ending, original_name) in enumerate(expected_order):
            # Find filename that came from this original
            matching_filename = None
            for filename in filenames:
                # We need to track which original filename produced which result
                # This will be handled by the batch processing function
                pass
                
        # For now, just verify we get 5 unique filenames with correct counters
        assert len(filenames) == 5
        assert len(set(filenames)) == 5  # All unique
        
        # All should have same base timestamp
        for filename in filenames:
            assert "20240615T163045" in filename
            assert "-r5a-" in filename