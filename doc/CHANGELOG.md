# Galleria Changelog

## 2025-10-27

### CDN Integration Preparation Completed
- **Relative URL system**: Simplified URL generation to use `photos/web/photo.jpg` instead of absolute paths
- **Dev server update**: Added support for relative photo paths alongside existing `/photos/` routes
- **CDN documentation**: Created `doc/bunnycdn-setup.md` with comprehensive setup guide
- **Configuration cleanup**: Removed complex CDN toggle system in favor of simple relative URLs
- **Ready for deployment**: CDN integration prepared for when Hetzner bucket is configured

### Task Prioritization
- **EXIF timestamp correction**: Moved from post-deploy to next priority task
- **Documentation update**: Updated TODO.md with accurate completion status and next steps

## 2025-10-15

### Build & Deployment Pipeline Completed
- **Deploy command**: Added full deploy command with photos-only, site-only, dry-run options
- **Shared service layer**: Created reusable `deploy_directory_to_s3()` function for DRY architecture
- **Build refactoring**: Extracted pure `build_gallery()` function with TDD approach
- **Directory structure**: Removed `PROCESSED_DIR` setting, standardized on `prod/pics/` for photos
- **Test fixes**: Fixed all command tests after directory structure cleanup
- **Pipeline ready**: Full automated build and deployment pipeline operational

### Base32 Counter Filename System
- **UTC normalization**: Replaced timezone offsets with UTC timestamps (removes + signs)
- **Base32 counters**: Implemented lexical base32 counter (0-V) instead of 3-digit numbers
- **Subsecond ordering**: Added hierarchy for same-timestamp photos using EXIF microseconds, subsecond tags, filename hints, and filesystem metadata
- **Batch processing**: Camera-first grouping prevents burst sequence interleaving
- **Filename optimization**: Reduced length from 47 to 33 characters (29% shorter)
- **Cross-platform compatibility**: Eliminated filesystem-problematic characters

### Development Server Photo Display
- **Photo serving fix**: Fixed thumbnail format detection (JPG vs WebP)
- **MIME type support**: Added proper content-type headers for .webp, .jpg, .jpeg, .png
- **PhotoMetadataService**: Fixed URL generation to check for WebP thumbnails first
- **Dev server routing**: /photos/* now correctly serves from prod/pics/*

### Gallery Chronological Ordering
- **PhotoMetadataService fix**: Updated regex pattern to match new filename format (collection-YYYYMMDDTHHMMSS-camera-counter.jpg)
- **Filename sorting**: Added chronological sorting to maintain photo order in gallery
- **Field mapping**: Changed 'sequence' to 'counter' to match base32 format
- **Gallery display**: Fixed photo ordering in static gallery generation

### Static Site Templates
- **Base template**: Created base.j2.html with navbar, proper HTML structure
- **Landing page**: Added index.j2.html with Christine & Marcus wedding info, privacy notice
- **Navigation**: Implemented navbar with Home/Gallery links and photo count
- **Build integration**: Updated build command to generate both index.html and gallery.html
- **Template comments**: Added HTML comments showing component boundaries for debugging

### Collection Analysis Command
- **collection-stats command**: New CLI tool for analyzing photo collections
- **Time analysis**: Full timeline analysis (10 hours), timezone extraction from EXIF
- **Camera detection**: Identified 2 cameras (5W/4F prefixes) across 645 photos
- **File size stats**: Storage analysis for full/web/thumbnail collections
- **Timezone discovery**: Found 4-hour systematic offset in camera timestamps

### EXIF Timezone Support
- **TDD implementation**: Added timezone extraction tests to EXIF service
- **get_timezone_info function**: Extracts OffsetTimeOriginal/OffsetTimeDigitized from EXIF
- **Piexif integration**: Added timezone EXIF tags to test fixture
- **Collection analysis**: Integrated timezone info into collection-stats output

### Documentation System
- **Command documentation**: Created doc/command/ directory with comprehensive CLI docs
- **collection-stats docs**: Detailed usage, examples, troubleshooting guide
- **Documentation index**: Updated doc/README.md to reference command documentation
- **Usage examples**: Development vs production workflows documented

### TODO Reorganization
- **JavaScript deferral**: Moved modal and interactive features to post-deployment
- **Deployment priority**: Updated TODO to prioritize static gallery and deployment pipeline
- **EXIF correction planning**: Documented timezone correction system for post-deploy
- **Storage architecture**: Defined archive vs production bucket separation

## 2025-10-14

### Hot-Reload Development Server
- **TDD implementation**: 14 tests covering server functionality, routing, and file watching
- **Custom HTTP handler**: /gallery route serves gallery.html, root returns 404 without index.html
- **File watcher**: Auto-rebuild on template/CSS/JS changes using watchdog library
- **Photo serving**: /photos/* routes map to prod/pics/* with proper MIME types
- **Build integration**: Fixed template path from templates/ to src/template/

### Photo Grid Component
- **Component-based templates**: Created photo-grid.j2.html using photo-cell includes
- **Grid responsiveness**: Configurable grid classes for different screen sizes
- **Gallery integration**: Updated gallery.j2.html to use photo-grid component
- **Template debugging**: Added debugging utilities for template development

### Photo Cell Component  
- **TDD template development**: Created photo-cell.j2.html with BeautifulSoup4 testing
- **Interactive elements**: Click handlers for photo modal integration
- **Responsive design**: Aspect-square containers with hover effects
- **Image optimization**: Object-cover for consistent thumbnail display

## 2025-10-13

### Build Command Started with TDD Approach
- **Build command**: Basic CLI structure with status reporting
- **Site generator service**: Directory checking and creation functionality
- **TDD separation of concerns**: Command handles terminal I/O, service handles actual work
- **Directory structure**: Creates prod/site/ with css/ and js/ subdirectories
- **Idempotent operation**: Detects existing directories and reports appropriately

## 2025-10-12

### Photo Processing Pipeline Complete
- **process-photos command**: Dual collection processing with full and web-optimized photos
- **Collection validation**: Ensures 1:1 matching between full and web collections  
- **Idempotent processing**: Skips unchanged photos using timestamp comparison
- **Real-world validation**: Successfully processed 645 wedding photos without sequencing errors
- **S3 storage service**: Complete implementation with moto testing for upload operations

## 2025-10-08

### Data Models & JSON Persistence (Completed)
- Created ProcessedPhoto, CameraInfo, and ExifData dataclass models
- Implemented JSON serialization/deserialization helpers
- Added photo_from_exif_service for model creation from EXIF data
- Integrated models with find-samples command for JSON output
- Full test coverage for all model operations

### Human-Readable Filename Generation (Completed)
- Replaced UUID system with human-readable chronological filenames
- Format: collection-YYYYMMDDTHHmmss.sssZhhmm-camera-seq.jpg
- Implemented GPS-to-timezone conversion using timezonefinder
- Added burst sequence number handling for duplicate timestamps
- Replaced pytz with Python's built-in zoneinfo module
- Created comprehensive test suite for all filename scenarios

### File Processing Pipeline (Completed)
- Implemented link_photo_with_filename using symlinks (not copies)
- Created WebP thumbnail generation with aspect ratio preservation
- Built process_photo_collection orchestration function
- Added burst mode sequence number increment logic
- Comprehensive error handling and idempotent operations
- Full test coverage including edge cases

### Documentation
- Created FUTURE.md for post-MVP features
- Updated symlink behavior to default (copy option deferred)

## 2025-10-07

- Fixed failing settings test for local settings override
- Test now correctly expects relative path override from local settings
- Resolved test_local_settings_override_defaults assertion error

## 2025-10-04

- Created manage.py entry point for Django-style command interface
- Added TDD tests for manage.py shell commands with subprocess execution
- Implemented extract_filename_sequence() for numeric camera filename parsing
- Enhanced chronological sorting to use numeric sequence instead of alphabetical
- Fixed multi-camera "three cycles" issue with proper timestamp+sequence sorting
- Added comprehensive real-world validation tests with realworld pytest marker
- Analyzed wedding photo collection: discovered dual Canon EOS R5 setup (4F6A/5W9A prefixes)
- Added performance testing infrastructure for large photo collections
- Updated E2E tests to test actual shell interface instead of Click commands directly
- Documented multi-camera findings and TEST_OUTPUT_PATH requirement in TODO.md
- Completed EXIF Service Module - E2E Testing & Real-world Validation phase

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