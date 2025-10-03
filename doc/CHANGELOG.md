# Galleria Changelog

## 2025-10-03

- Completed E2E testing for EXIF service integration
- Fixed burst detection to require same camera
- Fixed camera diversity sorting with None values
- Added command-level tests for find_samples
- All edge cases now properly handled with TDD coverage
- Findings: Burst detection is slightly over-eager but acceptable
  as chronological sequencing accuracy is the priority

## 2025-10-01

- Integrated EXIF service with find_samples command
- Added --show-bursts flag to display burst sequences
- Added --show-conflicts flag for timestamp conflicts
- Added --show-missing-exif flag for photos without EXIF
- Added --show-camera-diversity flag for camera breakdown
- Completed entire EXIF service module - removed from TODO.md
- Implemented EXIF service module Phase 5 - edge case detection
- Added find_timestamp_conflicts to identify multi-photographer scenarios
- Added find_missing_exif_photos to identify photos without timestamps
- Added get_camera_diversity_samples for camera diversity analysis
- Implemented EXIF service module Phase 4 - burst detection
- Added is_burst_candidate to check if photos are burst candidates
- Added detect_burst_sequences to group burst sequences
- Supports both subsecond and second-precision burst detection
- Implemented EXIF service module Phase 3 - chronological sorting
- Updated sort_photos_chronologically to include camera info in results
- Sorting now prioritizes: timestamp → camera make/model → filename
- Better handling of multi-photographer scenarios at same timestamp
- Implemented EXIF service module Phase 2 - timestamp utilities
- Added combine_datetime_subsecond to merge datetime with subsecond precision
- Added has_subsecond_precision to check for subsecond EXIF support

## 2025-09-26

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