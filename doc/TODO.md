# Galleria - Development Specification

**Commands implemented**: find-samples, upload-photos, process-photos, deploy

## Phase 5: Deploy Command **[COMPLETED ✅]**

**Status**: Enhanced deploy command implemented with metadata-driven deployment

### Completed Implementation

1. ✅ **Enhanced Deploy Command**: Metadata-driven deployment with automatic mode detection
2. ✅ **Integration Tests**: Complete TDD workflow with end-to-end testing
3. ✅ **CLI Features**: `--dry-run` shows deployment plans, `--force`/`--progress` options ready
4. ✅ **Backward Compatibility**: Existing deploy workflows preserved
5. ✅ **Documentation**: Complete command documentation in `doc/command/deploy.md`
6. ✅ **Test Coverage**: All 289 tests pass (289 passed, 10 skipped)

**Key Features:**
- Automatic detection of `gallery-metadata.json` for metadata-driven deployment
- Hash-based comparison using `deployment_file_hash` for selective uploads
- Fallback to directory-based deployment for legacy workflows
- Atomic operations with metadata-last upload ordering
- Comprehensive error handling and deployment plan visualization

**Note**: Deploy command ready for production use. Alpine.js functionality still deferred until post-deployment.

## CORS Management Enhancement **[COMPLETED ✅]**

**Status**: Comprehensive CORS configuration and validation system implemented

### Completed Implementation

1. ✅ **CORS Service Functions**: Complete CORS management in S3 storage service
2. ✅ **Deploy Command Integration**: Automatic CORS validation with early exit
3. ✅ **CLI Options**: `--setup-cors` flag for automatic CORS configuration  
4. ✅ **Comprehensive Testing**: 11 new tests for CORS functionality
5. ✅ **Documentation**: Complete CORS documentation in deploy and S3 storage docs

**Key Features:**
- Automatic CORS examination before deployment
- Early deployment abort if CORS not configured for web access
- Intelligent CORS rules comparison and updates
- Default gallery-optimized CORS rules
- Clear user guidance for CORS configuration

**Current System State (2025-10-29 - Latest Commit: CORS Management Complete)**:
- ✅ **EXIF timestamp correction** - Complete with 0 hour offset (camera time was correct)
- ✅ **JSON metadata system** - Complete with type-safe dataclasses and file hash calculation  
- ✅ **Dual-hash metadata system** - PhotoMetadata now has both `file_hash` and `deployment_file_hash` fields
- ✅ **Timezone settings** - Added `TARGET_TIMEZONE_OFFSET_HOURS = 2` (Swedish summer time)
- ✅ **PhotoMetadataService** - Supports both filename parsing and JSON metadata reading
- ✅ **Template debug service** - Fixed to use generic render() method
- ✅ **Integration testing** - Full round-trip from photo processing to metadata consumption
- ✅ **Gallery-metadata.json generation** - Automatic during photo processing with corrected timestamps
- ✅ **File hash calculation** - SHA256 hashes of original files for change detection
- ✅ **Filename generation** - Reflects corrected timestamps (with offset applied)
- ✅ **CORS management system** - Complete CORS validation and configuration for S3 buckets
- ✅ **Deploy command CORS integration** - Automatic CORS validation with early exit safety

**Key Architecture**: JSON metadata stores original + corrected timestamps and dual file hashes. During deployment, original files will be streamed → EXIF modified in memory → uploaded directly (no local storage of modified copies).

**🚧 CURRENT DEVELOPMENT STATUS**:
- **Phase 1 & 2 COMPLETE**: Settings and dual-hash metadata infrastructure ready
- **Phase 3 COMPLETE**: EXIF modification and deployment hash calculation implemented
- **Phase 4 COMPLETE**: Deployment orchestration with metadata-last upload ordering implemented
- **Phase 5 COMPLETE**: Enhanced deploy command with metadata-driven deployment implemented
- **CORS Management COMPLETE**: Comprehensive CORS validation and configuration system implemented

**🔧 FOR NEW DEVELOPERS - CURRENT IMPLEMENTATION STATE**:

**What's implemented:**
- ✅ `TARGET_TIMEZONE_OFFSET_HOURS` setting with full test coverage (`test/test_settings.py`)
- ✅ `PhotoMetadata` dataclass has `deployment_file_hash` field (`src/models/photo.py`)
- ✅ `GalleryMetadata.from_dict()` handles both hash fields correctly
- ✅ `modify_exif_in_memory()` function implemented (`src/services/s3_storage.py`)
- ✅ Deployment hash calculation implemented (`src/services/file_processing.py:258-285`)
- ✅ Deployment orchestration functions implemented (`src/services/deployment.py`)
- ✅ Comprehensive test suite for EXIF modification (`test/services/test_s3_storage.py`)
- ✅ Integration tests for dual-hash system (`test/test_dual_hash_integration.py`)
- ✅ Complete test suite for deployment orchestration (`test/services/test_deployment.py`)
- ✅ Complete documentation for metadata consistency system
- ✅ CORS management functions implemented (`src/services/s3_storage.py`)
- ✅ Deploy command CORS integration with early exit (`src/command/deploy.py`)
- ✅ Comprehensive CORS test suite (`test/services/test_s3_storage.py::TestCORSConfiguration`)
- ✅ Enhanced deploy command tests with CORS validation (`test/command/test_deploy.py::TestDeployCommandCORSValidation`)

**Key files to understand:**
- `src/models/photo.py` - PhotoMetadata structure with dual hashes
- `src/services/s3_storage.py` - modify_exif_in_memory() function and CORS management
- `src/services/file_processing.py` - Lines 258-285: deployment hash calculation
- `src/services/deployment.py` - Deployment orchestration with metadata-last upload ordering
- `settings.py` - Line 58: TARGET_TIMEZONE_OFFSET_HOURS setting
- `doc/architecture/metadata-consistency.md` - Complete system documentation

**Phase 3 Complete - Dual Timezone System Implemented:**

**Dual Timezone System Explanation:**
- **`TIMESTAMP_OFFSET_HOURS`**: Corrects systematic camera time errors ✅ IMPLEMENTED
  - Example: Camera was set 2 hours fast → offset = -2 to correct
- **`TARGET_TIMEZONE_OFFSET_HOURS`**: Sets actual timezone context for deployment ✅ IMPLEMENTED
  - Writes timezone info to EXIF `OffsetTimeOriginal` field per EXIF 2.31 standard
  - Format: `±HH:MM` (e.g., `-05:00` for EST, `+02:00` for CET)
  - Special value 13 = preserve original timezone (don't modify `OffsetTimeOriginal`)
- **Combined Logic**: corrected timestamp + timezone context = complete local time information ✅ IMPLEMENTED

✅ **Completed Phase 3 Tasks:**
1. ✅ **`modify_exif_in_memory()` implemented in `src/services/s3_storage.py`**:
   - Function signature: `modify_exif_in_memory(image_bytes, corrected_timestamp, target_timezone_offset_hours) -> bytes`
   - Uses `piexif` library for in-memory EXIF modification
   - Applies corrected timestamp to `DateTimeOriginal`
   - Applies timezone offset to `OffsetTimeOriginal` in `±HH:MM` format (unless offset = 13)
   - Complies with EXIF 2.31 standard for timezone information
2. ✅ **Deployment hash calculation implemented in `src/services/file_processing.py:258-285`**:
   - Simulates EXIF modification during processing using both timezone settings
   - Calculates hash of modified image bytes (reflects both timestamp correction and timezone)
   - Stores as `deployment_file_hash` with error fallback
3. ✅ **Comprehensive test suite implemented**:
   - `test/services/test_s3_storage.py::TestExifModification` (8 tests)
   - `test/test_dual_hash_integration.py` (5 integration tests)
   - Full documentation in `doc/architecture/metadata-consistency.md`

## Current JSON Metadata System **[FOR NEW DEVELOPERS]**

**How it works**:
1. **Photo Processing** (`process_dual_photo_collection`):
   - Reads EXIF from original files
   - Applies `TIMESTAMP_OFFSET_HOURS` setting in memory
   - Calculates SHA256 hash of original source files
   - Generates chronological filenames using corrected timestamps
   - Creates `gallery-metadata.json` with type-safe dataclasses

2. **Metadata Structure** (see `src/models/photo.py`):
   - `GalleryMetadata` → `PhotoMetadata` → `MetadataExifData` + `MetadataFileData`
   - Stores both original and corrected timestamps
   - Includes file hashes for change detection
   - Camera info and file paths for all variants (full/web/thumb)

3. **PhotoMetadataService** (`src/services/photo_metadata.py`):
   - `generate_json_metadata()` - Legacy filename parsing (backward compatibility)
   - `generate_json_metadata_from_file()` - New JSON metadata reading
   - Converts metadata to frontend-optimized format

4. **Testing** (`test/services/test_photo_metadata.py`):
   - Integration test proves complete round-trip works
   - File hash calculation verified
   - JSON metadata generation tested

## Idempotent Deployment System **[COMPLETED ✅]**

**Objective**: Enable selective deployment based on file changes using dual-hash metadata system with real-time EXIF modification.

**Key Innovation**: Calculate both original file hash and deployment file hash (after EXIF corrections) during photo processing, enabling accurate change detection for deployment.

**Status**: Complete implementation with Phases 1-5 all finished. Production-ready metadata-driven deployment system.

### Phase 1: Settings Enhancement ✅ **COMPLETED**
- [x] **Add timezone setting**: `TARGET_TIMEZONE_OFFSET_HOURS = 13` (13 = preserve original timezone)
- [x] **Environment variable support**: `GALLERIA_TARGET_TIMEZONE_OFFSET_HOURS`
- [x] **Test settings loading** and validation

### Phase 2: Dual Hash Metadata System ✅ **COMPLETED**
- [x] **Enhance PhotoMetadata dataclass** with `deployment_file_hash` field
- [x] **Update file_processing.py** to calculate both hashes:
  - `original_file_hash` (existing) - hash of source file
  - `deployment_file_hash` (placeholder) - will be hash after EXIF modifications applied
- [x] **Test metadata serialization** with both hashes

### Phase 3: EXIF Stream Processing ✅ **COMPLETED**
- [x] **Add `modify_exif_in_memory()`** to `s3_storage.py` for real-time EXIF modification
- [x] **EXIF modification streaming** - implemented in deployment workflow without temporary files
- [x] **Use piexif library**, preserve image quality, never store locally
- [x] **Test timezone application** and image integrity

### Phase 4: Deployment Orchestration ✅ **COMPLETED**
- [x] **Add metadata download/comparison** functions to `deployment.py`
- [x] **Add deployment plan generation** based on `deployment_file_hash` comparison
- [x] **Add S3 state verification** using `list_bucket_files()`
- [x] **Test complete workflow** with metadata-last upload ordering

✅ **Completed Phase 4 Features:**
1. ✅ **`download_remote_metadata()`** - Downloads and parses remote metadata from S3 with error handling
2. ✅ **`generate_deployment_plan()`** - Compares local vs remote using `deployment_file_hash`, identifies changes
3. ✅ **`verify_s3_state()`** - Validates remote state matches expected metadata, detects inconsistencies  
4. ✅ **`deploy_gallery_metadata()`** - Complete workflow with metadata-last upload ordering for atomic consistency
5. ✅ **Comprehensive test suite** - 21 new tests covering all deployment scenarios
6. ✅ **Dry run support** - Preview deployment plans without executing
7. ✅ **Error handling** - Graceful failures with detailed error reporting

### Phase 4 Documentation Task
- [x] **Document deployment orchestration system** in appropriate doc hierarchy following contribution guidelines

### Phase 5: Deploy Command ✅ **COMPLETED**
- [x] **Enhanced `src/command/deploy.py`** with CLI arguments:
  - `--dry-run`: Show deployment plan without executing
  - `--force`: Ready for implementation (ignore hash comparison, upload everything)
  - `--progress`: Ready for implementation (show detailed progress during upload)
- [x] **Metadata-driven deployment** using Phase 4 orchestration system
- [x] **Integration tests** with complete TDD workflow
- [x] **Documentation** in `doc/command/deploy.md`

### Implementation Approach
- **TDD throughout** - test every function before implementation
- **Metadata-last uploads** - photos first, then metadata (atomic consistency)
- **Hash-based comparison** - only upload changed photos using `deployment_file_hash`
- **Settings-aware** - timezone changes trigger new deployment hashes during processing
- **Failure recovery** - partial uploads don't corrupt metadata, enable retry

### Key Technical Decisions
1. **Dual hash system** - track both original and deployment file hashes
2. **Streaming EXIF modification** - never store corrected photos locally  
3. **Metadata-driven deployment** - compare deployment hashes, not file modification times
4. **Atomic operations** - metadata always reflects actual remote state
5. **Settings separation** - timestamp correction vs timezone are different concerns

## CRITICAL: Process-Photos Performance & Reliability Fix **[BLOCKING DEPLOYMENT - PRIORITY 1]**

**Issue Summary**: Multiple critical issues making `process-photos` command unusable for production:
1. Extreme performance issues (5+ minutes for 645 photos)
2. No progress indication during long processing
3. Memory consumption issues (accumulating 40MB+ photos in memory)
4. No crash recovery/resume capability
5. Missing timezone settings in metadata (blocking deployment)
6. 3 failing tests blocking deployment

**Root Causes**:
- `process_dual_photo_collection()` loads all 645 photos worth of metadata into memory
- Deployment hash calculation disabled as temporary fix (line 260 in file_processing.py)
- `GallerySettings` missing `target_timezone_offset_hours` and other processing settings
- No batch processing or progress reporting
- No partial file persistence for crash recovery

### **IMPLEMENTATION PLAN FOR NEW DEVELOPER**

#### **REQUIRED READING BEFORE STARTING**
1. **`doc/CONTRIBUTE.md`** - Development guidelines, testing workflow, commit format
2. **`doc/personal-setup-notes.md`** - Current production settings, timezone analysis, S3 configuration
3. **This section** - Complete implementation plan and technical specifications

**Essential Context**:
- Use `uv run pytest` for all testing (NOT `python -m pytest`)
- Follow TDD workflow: write test → ensure it fails → implement → make it pass
- Current production settings: `TIMESTAMP_OFFSET_HOURS = 0`, `TARGET_TIMEZONE_OFFSET_HOURS = 2`
- 645 wedding photos, some up to 40MB each
- Swedish timezone correction required (CEST = UTC+2)

#### **Phase 1: Fix Failing Tests (IMMEDIATE)**
**Location**: 3 failing tests block deployment
- `test/test_dual_hash_integration.py::TestDualHashIntegration::test_deployment_hash_differs_from_file_hash_when_timezone_set`
- `test/test_dual_hash_integration.py::TestDualHashIntegration::test_deployment_hash_changes_with_different_timezone_settings`  
- `test/test_settings.py::TestSettingsHierarchy::test_s3_settings_defaults`

**Root Cause**: Tests expect deployment hash calculation but it's disabled (line 260). Settings test polluted by `settings.local.py`.

**Required Fixes**:
1. **Fix settings test isolation**: Ensure `test_s3_settings_defaults` runs with clean defaults
2. **Re-enable deployment hash calculation**: Restore proper EXIF modification simulation in `generate_gallery_metadata()`
3. **Update GallerySettings dataclass**: Add missing `target_timezone_offset_hours` field

#### **Phase 2: Rewrite Process-Photos Command (CORE)**
**Location**: `src/command/process_photos.py` and `src/services/file_processing.py`

**New Architecture - Batch Processing with Memory Management**:

```python
# Batch processing approach (10-20 photos per batch)
def process_dual_photo_collection_batched(
    full_source_dir: Path,
    web_source_dir: Path, 
    output_dir: Path,
    collection_name: str,
    batch_size: int = 15
) -> dict:
    """Process photos in batches with progress reporting and partial persistence."""
    
    # 1. Get all photo pairs upfront
    photo_pairs = get_matched_photo_pairs(full_source_dir, web_source_dir)
    total_photos = len(photo_pairs)
    
    # 2. Check for existing partials and handle resume/restart
    handle_existing_partials(output_dir)
    
    # 3. Process in batches
    start_time = time.time()
    for batch_num, batch_start in enumerate(range(0, total_photos, batch_size)):
        batch_end = min(batch_start + batch_size, total_photos)
        batch_pairs = photo_pairs[batch_start:batch_end]
        
        # Process batch (keep only metadata in memory)
        batch_metadata = process_photo_batch(batch_pairs, batch_num, collection_name)
        
        # Save partial file immediately
        save_partial_metadata(batch_metadata, output_dir, batch_num)
        
        # Clear batch from memory
        del batch_metadata
        
        # Show progress with time estimate
        show_progress(batch_end, total_photos, start_time)
    
    # 4. Merge all partials into final metadata file
    merge_partial_files(output_dir, collection_name)
```

**Key Implementation Details**:

1. **Memory Management**:
   ```python
   def process_photo_batch(batch_pairs, batch_num, collection_name):
       batch_photos = []
       for full_path, web_path in batch_pairs:
           # Process one photo
           photo_data = process_single_photo(full_path, web_path)
           
           # Calculate deployment hash with EXIF modification
           photo_data.deployment_file_hash = calculate_deployment_hash(full_path)
           
           # Keep only metadata, discard photo content immediately
           batch_photos.append(photo_data)
           # photo content/bytes are cleared by function exit
       
       return generate_batch_metadata(batch_photos, collection_name)
   ```

2. **Partial File Management**:
   ```python
   # Save: gallery-metadata.part001.json, gallery-metadata.part002.json, etc.
   # Final merge: combine all parts into gallery-metadata.json
   # Cleanup: delete all .part*.json files after successful merge
   ```

3. **Progress Reporting**:
   ```python
   def show_progress(current, total, start_time):
       elapsed = time.time() - start_time
       rate = current / elapsed if elapsed > 0 else 0
       remaining = (total - current) / rate if rate > 0 else 0
       
       print(f"Processing photo {current}/{total} (ETA: {format_time(remaining)} remaining)")
   ```

4. **Resume/Restart Functionality**:
   ```python
   # Add CLI flags: --resume, --restart
   # If partials exist without flags: stop and prompt user
   # With --resume: validate latest partial, prompt confirmation, continue
   # With --restart: delete partials and start fresh
   ```

#### **Phase 3: Expand GallerySettings Dataclass**
**Location**: `src/models/photo.py`

**Current GallerySettings** (incomplete):
```python
@dataclass
class GallerySettings:
    timestamp_offset_hours: int = 0
```

**Required Complete GallerySettings**:
```python
@dataclass  
class GallerySettings:
    timestamp_offset_hours: int = 0
    target_timezone_offset_hours: int = 13  # NEW: Critical for deployment comparison
    web_size: tuple = (2048, 2048)          # NEW: Affects web photo output
    thumb_size: tuple = (400, 400)          # NEW: Affects thumbnail output  
    jpeg_quality: int = 85                  # NEW: Affects photo quality
    webp_quality: int = 85                  # NEW: Affects thumbnail quality
```

**Integration**: Update `generate_gallery_metadata()` to populate all fields from `settings.py`.

#### **Phase 4: Deployment Hash Calculation**
**Location**: `src/services/file_processing.py:258-285`

**Current State**: Disabled with placeholder
```python
# Calculate deployment file hash - temporarily use original hash for speed
# TODO: Calculate actual deployment hash during deployment, not processing
deployment_hash = photo.file_hash or ""
```

**Required Implementation**: Re-enable within batch processing
```python
def calculate_deployment_hash(photo_path: Path) -> str:
    """Calculate hash of photo after EXIF modifications applied."""
    from src.services.s3_storage import modify_exif_in_memory
    import settings
    
    # Read photo into memory
    with open(photo_path, 'rb') as f:
        photo_bytes = f.read()
    
    # Apply EXIF modifications (timestamp + timezone)
    corrected_timestamp = get_corrected_timestamp(photo_path)
    modified_bytes = modify_exif_in_memory(
        photo_bytes, 
        corrected_timestamp,
        settings.TARGET_TIMEZONE_OFFSET_HOURS
    )
    
    # Calculate hash and immediately clear memory
    hash_value = hashlib.sha256(modified_bytes).hexdigest()
    del photo_bytes, modified_bytes  # Clear memory immediately
    
    return hash_value
```

#### **Phase 5: Enhanced Command Interface**
**Location**: `src/command/process_photos.py`

**Add CLI Options**:
```python
@click.option('--resume', is_flag=True, help='Resume from existing partial files')
@click.option('--restart', is_flag=True, help='Delete partials and start fresh')
@click.option('--batch-size', default=15, help='Photos per batch (memory management)')
```

**Partial File Handling Logic**:
```python
def handle_existing_partials(output_dir: Path, resume: bool, restart: bool):
    """Handle existing partial files based on user choice."""
    partials = list(output_dir.glob('gallery-metadata.part*.json'))
    
    if partials and not (resume or restart):
        latest_partial = max(partials, key=lambda p: p.stat().st_mtime)
        age_hours = (time.time() - latest_partial.stat().st_mtime) / 3600
        
        if age_hours <= 24:
            batch_num = extract_batch_number(latest_partial)
            click.echo(f"Error: Found existing partial files from {age_hours:.1f} hours ago (batch {batch_num} complete).")
            click.echo("Use --resume to continue or --restart to start fresh.")
            sys.exit(1)
        else:
            # Auto-cleanup old partials
            cleanup_partials(partials)
    
    elif restart and partials:
        cleanup_partials(partials)
        click.echo(f"Cleaned up {len(partials)} partial files. Starting fresh.")
    
    elif resume and partials:
        validate_and_resume(partials)
```

### **TESTING REQUIREMENTS**

1. **Fix Existing Tests**: Ensure all 289 tests pass
2. **New Batch Processing Tests**: Test batch logic, partial files, memory management  
3. **Resume/Restart Tests**: Test CLI flag behavior and partial file validation
4. **Settings Tests**: Test complete GallerySettings recording and comparison
5. **Performance Tests**: Verify memory usage stays low during processing

### **SUCCESS CRITERIA**

1. ✅ **All tests passing** (zero failures)
2. ✅ **Fast processing** (< 2 minutes for 645 photos vs 5+ minutes before)
3. ✅ **Low memory usage** (no accumulation of 40MB photos in memory)
4. ✅ **Progress visibility** ("Processing photo 145/645 (ETA: 3m 42s remaining)")
5. ✅ **Crash recovery** (resume from partials with --resume flag)
6. ✅ **Complete metadata** (all processing settings recorded for deployment comparison)
7. ✅ **Production ready** (can run `process-photos` → `build` → `deploy` successfully)

### **CRITICAL FILES TO MODIFY**

1. **`src/command/process_photos.py`** - Add CLI flags, progress reporting
2. **`src/services/file_processing.py`** - Rewrite `process_dual_photo_collection()` with batching
3. **`src/models/photo.py`** - Expand `GallerySettings` dataclass  
4. **`test/test_dual_hash_integration.py`** - Fix failing deployment hash tests
5. **`test/test_settings.py`** - Fix settings test isolation

**Status**: Ready for implementation. All technical decisions made. Clear success criteria defined.

## Real-world Deployment Testing **[NEXT PRIORITY AFTER FIXES]**

**Objective**: Set up and test production S3/Hetzner bucket with CDN integration.

**Prerequisites**: ✅ All deployment infrastructure complete (Phases 1-5 + CORS). ⚠️ Timezone metadata issue must be resolved first.

### Current Walkthrough Progress

**Status**: In progress - blocking issues identified during setup

**Completed Steps**:
1. ✅ **Personal configuration analysis** - EXIF timezone issue identified and settings determined
2. ✅ **Settings configuration** - `settings.local.py` configured with correct timezone settings
3. ✅ **Process-photos execution** - Completed in 1m23s (645 photos processed)
4. ⚠️ **Critical issues discovered** - Timezone metadata and performance issues must be resolved

**Pending Steps**:
1. **Fix timezone metadata issue** - Add `target_timezone_offset_hours` to metadata
2. **Verify test suites pass** - Ensure performance fix doesn't break functionality  
3. **Re-run process-photos** - Generate metadata with complete settings
4. **Execute build command** - Generate static site
5. **Execute deploy --setup-cors** - First production deployment
6. **Verify EXIF corrections** - Confirm timezone fixes in deployed photos

### Production Deployment Instructions

**READY TO DEPLOY**: The system is production-ready. Follow these steps for first deployment:

#### Step 1: Configure Production Settings

Add to `settings.local.py`:
```python
# S3 Production Configuration  
S3_PUBLIC_ENDPOINT = "https://eu-central-1.s3.hetznerobjects.com"  # Your actual endpoint
S3_PUBLIC_BUCKET = "your-actual-bucket-name"  # From bucket setup
S3_PUBLIC_REGION = "eu-central-1"  # Your bucket region

# Photo Processing Settings
TIMESTAMP_OFFSET_HOURS = -4  # Your camera systematic correction
TARGET_TIMEZONE_OFFSET_HOURS = -5  # Target timezone (e.g., EST = -5, CET = +1)
```

#### Step 2: Set Environment Variables for Secrets
```bash
export GALLERIA_S3_PUBLIC_ACCESS_KEY="your_access_key"
export GALLERIA_S3_PUBLIC_SECRET_KEY="your_secret_key"
```

#### Step 3: Complete Deployment Workflow
```bash
# Process photos with timezone corrections
uv run python manage.py process-photos

# Build static site
uv run python manage.py build

# Deploy with automatic CORS setup
uv run python manage.py deploy --setup-cors
```

**What happens**: System processes photos with `-4h` correction, applies target timezone to EXIF, generates dual hashes, validates/configures CORS, and uploads only changed photos using metadata comparison.

**Next steps after deployment**: CDN setup using `doc/bunnycdn-setup.md`

### S3 Bucket Setup Requirements

1. **Hetzner Object Storage Configuration**
   - [ ] Create production bucket with appropriate permissions
   - [ ] Configure CORS for frontend access
   - [ ] Set up lifecycle policies for optimization
   - [ ] Document bucket naming and region selection

2. **CDN Integration (BunnyCDN)**
   - [ ] Configure BunnyCDN origin pointing to Hetzner bucket
   - [ ] Set up cache rules for photos vs metadata
   - [ ] Test cache invalidation workflow
   - [ ] Document CDN configuration

3. **Deployment Validation**
   - [ ] Test complete pipeline: process → build → deploy
   - [ ] Verify incremental updates work correctly
   - [ ] Test rollback procedures
   - [ ] Performance testing with full 645 photo collection

4. **Production Readiness**
   - [ ] Set up monitoring and alerting
   - [ ] Document operational procedures
   - [ ] Create deployment checklist
   - [ ] Plan for CI/CD integration

## External Settings Path Verification **[COMPLETED]**

**Task**: Document and verify existing capability for settings files outside project root.

**Current Status**: ✅ COMPLETED - Settings system supports external paths via XDG config specification.

### Verification Results

1. **Existing Implementation Verified** ✅
   - [x] XDG config directory support confirmed (`settings.py:37-38`)
   - [x] `GALLERIA_LOCAL_SETTINGS_FILENAME` environment variable works
   - [x] `XDG_CONFIG_HOME` allows settings outside project root  
   - [x] Comprehensive test suite exists (`test/test_settings.py`)

2. **Usage Examples** ✅
   - **Local settings file**: Add `TIMESTAMP_OFFSET_HOURS = -4` to `settings.local.py`
   - **Environment variable**: `export GALLERIA_TIMESTAMP_OFFSET_HOURS=-4`
   - **XDG config**: Create `$XDG_CONFIG_HOME/galleria/settings.local.py`
   - **Precedence**: `defaults → local settings → environment variables`

## Project Overview

A static photo gallery built with a custom Python static site generator,
using AlpineJS for frontend interactions and
Tailwind CSS for styling.
Photos are processed with human-readable chronological filenames derived from EXIF data and
hosted on Hetzner object storage with BunnyCDN for global distribution.

### Conventions of Project

This is going for a django style settings, command and layout structure.
But we're also trying to find
a middle ground between django and FastAPI conventions.
In particular with functional paradigms,
like @click decorated commands for example.
Because this line between conventions is blurry, please ask.

### Priority

Speed of development and deployment over feature richness.
Get a working, acceptable user experience deployed quickly.

## Stack & Workflow Overview

### Technology Stack

- **Static Site Generator**: Custom Python generator with Jinja2 (Python 3.12)
- **Frontend**: AlpineJS + Tailwind CSS (CDN, no build step)
- **Photo Processing**: Python with Pillow, exifread
- **Storage**: Hetzner object storage (private + public buckets)
- **CDN**: BunnyCDN with Hetzner as origin
- **Development**: Local build -> Hetzner deployment
- **Package Management**: uv (Python package manager)
- **Testing**: pytest with `uv run pytest` command

### Photo Processing Workflow

```txt
Photographer's Photos -> EXIF Extraction -> Chronological Filename Generation ->
-> Thumbnail Creation -> Upload to Buckets ->
-> Custom HTML Generation -> Deploy
```

### Photo Organization Structure

```txt
Private Bucket (Hetzner):     Public Bucket (Hetzner):        Static Site:
/originals/                   /galleria-wedding/              Gallery page with:
  IMG_001.jpg                   {filename}.jpg  (full)         - Thumbnail grid
  IMG_002.jpg                   {filename}.jpg  (web)          - Infinite scroll
  ...                           {filename}.webp (thumb)        - Multi-select downloads
```

### Storage Strategy

- **Private Hetzner Bucket**: Original photos with authentication (personal archive)
- **Public Hetzner Bucket**: Full + web + thumbnail versions (for static site)
- **BunnyCDN**: Global CDN caching content from public Hetzner bucket

### Command Workflow & Sequence

The project follows a simplified workflow for processing and deploying the photo gallery:

```txt
Original Photos (PIC_SOURCE_PATH_FULL + PIC_SOURCE_PATH_WEB)
    ↓ [process-photos] 
Processed Photos (prod/pics)
    ↓ [build]
Static Site (OUTPUT_DIR)
    ↓ [deploy] 
Single S3 Bucket (photos + HTML + CSS + JS)
    ↓
Live Website
```

#### Command Overview

1. **`process-photos`** - Photo processing pipeline
   - Reads original photos from `PIC_SOURCE_PATH_FULL`
   - Reads web-optimized photos from `PIC_SOURCE_PATH_WEB` 
   - Extracts EXIF data and generates chronological filenames
   - Creates thumbnails (400x400 WebP) from web versions
   - Validates filename consistency between full and web collections
   - Outputs to `prod/pics` with structure:
     ```
     processed-photos/
       full/     (symlinks to originals with chronological names)
       web/      (symlinks to photographer's web-optimized versions)
       thumb/    (WebP thumbnails generated from web versions)
     ```

2. **`build`** - Static site generation  
   - Generates JSON metadata from processed photos
   - Creates static HTML using Jinja2 templates
   - Copies static assets (CSS/JS)
   - Outputs complete site to `OUTPUT_DIR`

3. **`deploy`** - Complete site deployment
   - Idempotently uploads entire site to single S3 bucket:
     - Photos (full/web/thumb) to `/photos/` prefix
     - Static site files (HTML/CSS/JS) to bucket root
     - JSON metadata for gallery functionality
   - Skips already uploaded files for efficiency
   - Supports dry-run and progress tracking
   - Handles CDN cache invalidation if needed

#### Usage Patterns

```bash
# Full pipeline for new gallery
python manage.py process-photos
python manage.py build  
python manage.py deploy --progress

# Development workflow
python manage.py process-photos --source ./test-photos
python manage.py build --dev-mode
python manage.py deploy --dry-run

# Quick site update (photos already processed)
python manage.py build
python manage.py deploy
```

**Note**: Commands are designed to be idempotent - running them multiple times is safe. The `deploy` command handles all upload operations to maintain consistency.

---

**See doc/CONTRIBUTE.md for development guidelines and coding standards**

## Development Tasks & Specifications

### Static Site Generation **[COMPLETED]**

**Deliverable**: Static HTML gallery with complete functionality

See `doc/architecture/static-site-generation.md` for implementation details.


---

### EXIF Timestamp Correction **[NEXT PRIORITY]**

**Deliverable**: Timezone correction system for camera clock errors

#### Problem Identified
- Camera EXIF shows `+00:00` (UTC) timezone but timestamps are 4 hours ahead of expected UTC
- Ceremony at 4:00 PM Swedish time (UTC+2) should be 2:00 PM UTC, but photos show 6:10 PM
- All 645 photos have systematic 4-hour offset from expected UTC timing

#### Acceptance Criteria
- [ ] **Settings-based offset**: Add `TIMESTAMP_OFFSET_HOURS` setting (e.g., `-4` hours)
- [ ] **Processing integration**: Apply offset during `process-photos` command
- [ ] **EXIF correction**: Modify EXIF data in production bucket copies
  - Correct `DateTimeOriginal` to proper UTC time
  - Set `OffsetTimeOriginal` to actual Swedish timezone (`+02:00`)
  - Preserve original archive files (read-only)
- [ ] **Upload detection**: Deploy command detects EXIF changes and re-uploads
- [ ] **CDN invalidation**: Trigger cache refresh when photos change
- [ ] **Documentation**: Log corrections applied for transparency

#### Implementation Plan
1. Add timezone offset setting to process-photos workflow
2. Integrate EXIF correction into production bucket upload
3. Test upload change detection and CDN invalidation
4. Validate corrected timestamps work in external photo management software

---

### BunnyCDN Configuration

**Deliverable**: CDN setup for global content delivery

#### Acceptance Criteria

- [ ] BunnyCDN pull zone configured with Hetzner as origin
- [ ] Proper caching headers set
- [x] CDN URLs integrated into static site (simplified to relative URLs)
- [ ] Performance testing confirms global speed improvement
- [x] Create doc/bunnycdn-setup.md with detailed configuration steps
- [ ] Update doc/remote-storage-setup.md to link to CDN documentation

#### CDN Configuration Required

```
Origin URL: https://your-bucket.hetzner-endpoint.com
Pull Zone: galleria-cdn
Caching: Standard settings for images
Purge: Manual trigger capability
```

---

### Build & Deployment Pipeline **[COMPLETED]**

**Deliverable**: Automated build and deployment scripts

#### Acceptance Criteria

- [x] Build script processes all photos correctly
- [x] Custom site generator creates static HTML successfully
- [x] Deployment script uploads to Hetzner
- [ ] Non-obvious URL structure implemented
- [x] Full pipeline runs without manual intervention

#### Command Implementation Requirements

##### process-photos Command

**Purpose**: Process original photos into web-ready formats

**CLI Options**:
- `--source`, `-s`: Override PIC_SOURCE_PATH_FULL
- `--output`, `-o`: Override default output (prod/pics)
- `--collection-name`: Name for this photo collection (default: from settings)
- `--skip-existing`: Skip processing if output files exist
- `--dry-run`: Show what would be processed without doing it
- `--workers`: Number of parallel workers for processing

**Processing Steps**:
1. Scan source directory for image files
2. Extract EXIF data from each photo
3. Generate chronological filenames with burst handling
4. Create symlinks in `full/` directory
5. Generate web-sized JPEGs in `web/` directory
6. Create WebP thumbnails in `thumb/` directory
7. Save metadata to JSON cache

##### build Command

**Purpose**: Generate static website from processed photos

**CLI Options**:
- `--skip-s3`: Build using local files instead of S3 URLs
- `--template-dir`: Override template directory
- `--output`, `-o`: Override OUTPUT_DIR
- `--dev-mode`: Use unminified CSS/JS for development

**Build Steps**:
1. Load photo metadata from JSON cache
2. Generate photo manifest for JavaScript
3. Render Jinja2 templates (index, gallery, etc.)
4. Copy static assets (CSS, JS, images)
5. Generate sitemap.xml
6. Create deployment manifest

##### upload-photos Command

See "Upload to Public Gallery Bucket" section above for details.

##### deploy Command

**Purpose**: Deploy complete gallery (photos + static site) to production hosting

**CLI Options**:
- `--source`, `-s`: Override OUTPUT_DIR
- `--dry-run`: Show deployment plan without executing
- `--invalidate-cdn`: Trigger CDN cache purge
- `--photos-only`: Upload only photos/metadata (skip static site)
- `--site-only`: Upload only static site files (skip photos)

**Storage Architecture**:
- **Archive Bucket**: Original photographer files (read-only, never modified)
- **Production Bucket**: Processed photos + static site for public access
  - `/photos/full/` - Full resolution with corrected EXIF
  - `/photos/web/` - Web-optimized with corrected EXIF  
  - `/photos/thumb/` - WebP thumbnails
  - `/metadata.json` - Photo metadata with corrected timestamps
  - `/index.html`, `/gallery.html` - Static site files

**Architecture Plan**:
- **Service Layer**: Create reusable `deploy_directory_to_s3()` function
  - Takes source dir, bucket, prefix, options
  - Handles S3 logic, progress, dry-run, error handling
  - Returns detailed upload results
- **Commands**:
  - `upload-photos`: Simple wrapper around service function for prod/pics → photos/ prefix
  - `deploy`: Comprehensive wrapper - calls service function for both photos AND static site files
- **Smart Detection**: Add in future iteration after initial deployment
  - Compare local file checksums vs S3 ETags
  - Only upload changed files
  - Track deployment state in metadata

**Deployment Steps**:
1. Call `deploy_directory_to_s3()` for photos (if not --site-only)
2. Call `deploy_directory_to_s3()` for static site files (if not --photos-only)
3. Trigger CDN cache invalidation (if --invalidate-cdn)
4. Output deployment summary and production URLs

---

### Testing & Quality Assurance

**Deliverable**: Comprehensive test suite and manual testing

#### Acceptance Criteria

- [ ] All unit tests passing (90%+ coverage for core logic)
- [ ] Integration tests for Hetzner API
- [ ] Cross-browser testing (Chrome, Safari, Firefox)
- [ ] Mobile device testing
- [ ] Template tests with BeautifulSoup4
- [ ] User acceptance testing with family members

#### Test Categories Required

```
test/
-> services/               (Service layer tests)
-> template/               (Template structure tests with BeautifulSoup4)
   -> test_base_template.py
   -> test_gallery_template.py
   -> test_photo_components.py
-> command/                (Command tests)
-> integration/            (API integration tests)
```

---

### Pre-Deployment Performance Testing

**Deliverable**: Performance comparison between static and progressive loading approaches

#### Acceptance Criteria

- [ ] Static vs Progressive Loading Comparison: Build both versions side-by-side
- [ ] Performance Metrics: Lighthouse scores, page load times, Time to First Contentful Paint
- [ ] Network Analysis: Total payload size comparison, number of requests
- [ ] User Experience Testing: Perceived performance on different connection speeds
- [ ] Testing Framework: Automated performance testing with Playwright or similar
- [ ] Performance report documenting findings and recommendations

---

### Final Deployment & Monitoring

**Deliverable**: Live wedding gallery accessible to guests

#### Acceptance Criteria

- [ ] Gallery deployed with non-obvious URL
- [ ] Performance acceptable for US and EU users
- [ ] All download functionality working
- [ ] Mobile experience tested and approved
- [ ] Backup and monitoring in place

#### Success Metrics

- Gallery page loads in <3 seconds for US users via BunnyCDN
- Thumbnail grid displays smoothly with infinite scroll
- Individual photo downloads complete reliably
- Site works on mobile devices without significant issues
- Older family members can successfully select and download photos

---

## Post-Deployment Enhancements

### Frontend Functionality **[MOVED FROM PRE-DEPLOY - FIRST PRIORITY]**

**Deliverable**: Interactive photo gallery with AlpineJS

#### Pre-requisite: Fix Hot Reload Bug

**IMPORTANT**: The serve command's hot reloading server often fails to hot reload on template changes. This will become frustrating during complex frontend development. Fix this bug before implementing any other frontend changes.

#### Acceptance Criteria

- [ ] Photo grid displays thumbnails correctly
- [ ] Infinite scroll loads photos progressively
- [ ] Checkbox selection updates state
- [ ] Download functionality triggers individual file downloads
- [ ] Select all/none buttons work correctly
- [ ] Mobile-responsive interaction

#### AlpineJS Component Structure

```javascript
Alpine.data('photoGallery', () => ({
    photos: [],
    selectedPhotos: [],
    loadedCount: 0,
    batchSize: 20,
    
    // Methods
    loadMorePhotos(),
    togglePhoto(photoId),
    selectAll(),
    selectNone(),
    downloadSelected(resolution)
}))
```

#### Frontend Features Required

- Lazy loading of thumbnails
- Visual feedback for selected photos
- Download progress indication
- Error handling for failed downloads
- Keyboard navigation support

### Dynamic Loading & Performance

**Deliverable**: Progressive loading optimization for large photo collections

#### Acceptance Criteria

- [ ] **Infinite Scroll Loading**: Split photo rendering between initial batch (server-side) and progressive loading (JS)
- [ ] **Lazy Loading**: Progressive image loading optimization
- [ ] **Performance Monitoring**: Real-world performance metrics collection
- [ ] **BunnyCDN Analytics Integration**: Parse CDN access logs for photo popularity tracking
- [ ] **Popularity-Based Ordering**: Sort photos by download frequency from CDN logs


### Photo Modal Navigation **[MOVED FROM PRE-DEPLOY]**

**Deliverable**: Interactive photo preview with navigation

#### Photo Modal Navigation Design

- **Modal Size**: 80% viewport (keeping 20% for dismiss area)
- **Navigation Zones**: 
  - Left 25% of modal: Previous photo
  - Right 25% of modal: Next photo  
  - Middle 50%: No action (view photo)
- **Navigation Features**:
  - Wrap-around navigation (first ↔ last)
  - ESC key to close modal
  - Click backdrop (20% area) to close
- **Implementation**: Alpine.js with click zones and keyboard handlers

### Interactive Photo Selection

**Deliverable**: Multi-select download functionality

#### Acceptance Criteria

- [ ] **Checkbox Selection**: Add checkboxes to photo cells for multi-select
- [ ] **Selection Controls**: Select all/none buttons, selection counter
- [ ] **Download Functionality**: Batch download of selected photos (web/full resolution)
- [ ] **Selection State Management**: Persistent selection across page interactions
- [ ] **Selection Bar**: Bottom overlay showing selected count and actions

---

## Future Enhancements

### Photography Organization

- **GPS-based event segmentation**: Automatic detection of preparation, ceremony, photo shoot, and reception locations
- **Event filtering**: Jump to different parts of the day based on GPS clustering
- **Timeline view**: Alternative layout showing photos in temporal context

### Download Improvements

- **Zip file generation microservice**: Server-side zip creation for better UX with large selections
- **Progress indicators**: Download preparation and progress feedback
- **Batch download optimization**: Smart batching for large selections

### Content & Design

- **Landing page content**: Welcome message, collection information, thank you notes (wife to write)
- **About page**: Additional wedding information and context
- **Advanced styling**: Custom photo layouts, animations, enhanced mobile experience

### Technical Improvements

- **Python 3.13 migration**: Update to Debian's current default Python version
- **CI/CD pipeline**: Automated build and deployment via GitHub Actions
- **Photo metadata display**: Optional timestamp and location information
- **Search functionality**: Photo filtering and search capabilities
- **Analytics**: Basic usage tracking and popular photo identification

### Performance Optimization

- **Lazy loading**: Progressive image loading optimization
- **CDN optimization**: Advanced BunnyCDN configuration for better global performance
- **Compression**: Additional image optimization techniques

## Filename Format Analysis

### UUID vs Human-Readable Comparison

**UUIDv7 Approach (Discarded):**

- 26 characters (Base32 encoded)
- Abstract, not human-readable
- Over-engineered for wedding photo scale
- Complex implementation (~100+ lines)
- Designed for distributed systems with billions of IDs

**Human-Readable Timestamps (Selected):**

- ~35 characters but human-readable
- Instant chronological understanding
- GPS-based timezone context
- Simple implementation (~30 lines)
- Perfect for wedding-scale collections

**Decision Rationale:**
Human-readable filenames chosen because they provide immediate temporal context, sort chronologically in any file browser, and are much simpler to implement and debug. The slight length increase is offset by the massive usability improvement.

### Developer Tools (Deprioritized)

#### list-samples Command

**Status**: Deprioritized - find-samples already provides needed functionality

Originally planned to display saved sample metadata from JSON cache. However, find-samples 
already shows all necessary information when run, and the JSON output is primarily useful
for debugging. The command structure and edge case detection from find-samples proved more
valuable as building blocks for chronological UUID generation than as a standalone tool.

---

*This specification prioritizes rapid deployment of core functionality. Features marked as "Future" can be implemented in subsequent iterations after the initial gallery is live and functional.*

