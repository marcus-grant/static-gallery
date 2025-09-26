# Galleria Changelog

## 2025-09-26

- Implemented EXIF service module Phase 2 - timestamp utilities
- Added combine_datetime_subsecond to merge datetime with subsecond precision
- Added has_subsecond_precision to check for subsecond EXIF support
- Implemented EXIF service module Phase 1 with core extraction helpers
- Added extract_exif_data function for raw EXIF dictionary extraction
- Added get_datetime_taken function to parse DateTimeOriginal timestamps
- Added get_subsecond_precision function for burst mode detection
- Added get_camera_info function to extract make and model
- Created flexible test fixture for generating fake photos with EXIF data
- Added piexif dependency for EXIF manipulation in tests

## 2025-09-25

- Implemented hierarchical settings system (CLI > env vars > local > defaults)
- Added GALLERIA_ prefix for all environment variables
- Implemented local settings override via settings.local.py
- Added XDG Base Directory compliance for config and cache directories
- Established test coverage for settings precedence hierarchy
- Started command infrastructure with find-samples command
- Added CLI argument override testing for commands
- Completed file system service module with ls_full function
- Added fs module tests for directory scanning and image file detection
- Integrated fs module with find_samples command