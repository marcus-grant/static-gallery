# Galleria - Development Specification

**Commands implemented**: find-samples, upload-photos, process-photos

## Current Test Failures **[IMMEDIATE PRIORITY]**

**Status**: 8 failing template tests after CDN URL changes (233 passing, 4 skipped)

### Identified Bugs

1. **Template URL Expectations** - Tests expect `/photos/` URLs but code now generates relative `photos/` URLs
   - Affected: `test_photo_cell_component.py`, `test_photo_grid_component.py`
   - Root cause: URL format change in `PhotoMetadataService`

2. **Missing Alpine.js Integration** - Templates missing Alpine.js CDN and initialization
   - Affected: `test_base_template.py`, `test_gallery_template.py`
   - Root cause: Alpine.js functionality not implemented in templates

3. **Template Debug Service Issues** - Missing `render_photo_cell` method
   - Affected: `test_template_debug.py`
   - Root cause: TemplateRenderer missing photo cell rendering method

4. **Photo Component Rendering** - Photo cells and grids not rendering properly
   - Affected: Multiple photo component tests
   - Root cause: Alpine.js missing + URL format mismatch

### Fix Priority
- [x] Update template tests to expect relative URLs (`photos/` not `/photos/`)
- [ ] **DEFER Alpine.js tests** - These test future JS functionality, not current static MVP
- [ ] Implement missing TemplateRenderer.render_photo_cell method  
- [ ] **Focus on static site first** - Skip JS-related test failures until post-deploy

**Note**: Alpine.js functionality is planned for post-deployment. Current priority is JSON metadata system.

**Recent Completed Work**:
- ✅ EXIF timestamp correction implemented and tested (56 tests pass)
- ✅ CDN integration with relative URLs (`photos/web/photo.jpg` not `/photos/`)
- ✅ Dev server supports both `/photos/` and `photos/` paths  
- ✅ Template tests fixed for URL format changes
- ✅ Alpine.js functionality deferred until post-deployment
- ✅ Static-first approach: Pure HTML gallery without JavaScript

## EXIF Timestamp Correction **[COMPLETED]**

**Problem**: Camera EXIF shows `+00:00` (UTC) timezone but timestamps are 4 hours ahead of expected UTC. All 645 photos have systematic 4-hour offset.

**Goal**: Add `-4` hour offset setting and integrate into photo processing workflow.

**✅ IMPLEMENTATION COMPLETE** - Key details for next developer:
- Offset applied during EXIF reading in `get_datetime_taken()` (not file modification)
- Uses `timedelta(hours=offset)` for timestamp correction  
- All tests use `autouse` fixtures for proper isolation (`reset_timestamp_offset`)
- Original files remain unchanged (symlinks preserved in `prod/pics/`)
- Settings precedence: `defaults → local settings → environment variables`
- ⚠️ **CRITICAL**: Deploy step must copy files and modify EXIF in uploads (see "Deployment EXIF Modification" section below)

### Implementation Tasks

1. **Add Settings** (TDD approach)
   - [x] Write test for timestamp offset setting
   - [x] Add `TIMESTAMP_OFFSET_HOURS` to `settings.py` (defaults to 0)
   - [x] Add environment variable support: `GALLERIA_TIMESTAMP_OFFSET_HOURS`

2. **Modify EXIF Service** (TDD approach)
   - [x] Write test for offset application in `get_datetime_taken()`
   - [x] Update `src/services/exif.py` to apply offset
   - [x] Use JSON metadata for corrections (not actual EXIF file modification)

3. **Integrate into Photo Processing** (TDD approach)
   - [x] Write test for offset integration in processing workflow
   - [x] Verify offset flows through `process_dual_photo_collection`
   - [x] Preserve originals (symlinks remain unchanged)

4. **Testing & Validation**
   - [x] All tests pass with proper isolation using `autouse` fixtures
   - [x] Run comprehensive test suite validation (56 tests pass)
   - [x] Verify EXIF correction maintains chronological ordering with synthetic photos
   - [x] Test chronological filename generation with offset timestamps

5. **JSON Metadata System** (New Approach)
   - [ ] Design JSON schema for corrected timestamps and EXIF data
   - [ ] Generate `prod/gallery-metadata.json` during photo processing
   - [ ] Update build system to read from JSON metadata
   - [ ] Generate frontend-ready `prod/site/gallery-data.json`

## JSON Metadata & Idempotent Deployment **[NEXT PRIORITY]**

**Objective**: Implement JSON-based metadata system for EXIF corrections and enable selective deployment based on file changes.

**Benefits**:
- Separate EXIF corrections from photo storage
- Enable idempotent deployments (only upload changed files)
- Provide frontend-ready JSON for JavaScript gallery functionality
- Preserve original photos unchanged

### JSON Metadata Schema Design

**Local Metadata** (`prod/gallery-metadata.json`):
```json
{
  "schema_version": "1.0",
  "generated_at": "2024-10-27T14:30:45Z",
  "collection": "wedding",
  "settings": {
    "timestamp_offset_hours": -4
  },
  "photos": [
    {
      "id": "wedding-20240810T143045-r5a-0",
      "original_path": "pics-full/IMG_001.jpg",
      "file_hash": "sha256:abc123...",
      "exif": {
        "original_timestamp": "2024-08-10T18:30:45",
        "corrected_timestamp": "2024-08-10T14:30:45",
        "timezone_original": "+00:00",
        "timezone_corrected": "+02:00",
        "camera": {"make": "Canon", "model": "EOS R5"},
        "subsecond": 123
      },
      "files": {
        "full": "prod/pics/full/wedding-20240810T143045-r5a-0.jpg",
        "web": "prod/pics/web/wedding-20240810T143045-r5a-0.jpg", 
        "thumb": "prod/pics/thumb/wedding-20240810T143045-r5a-0.webp"
      }
    }
  ]
}
```

**Frontend JSON** (`prod/site/gallery-data.json`):
```json
{
  "collection": "wedding",
  "photos": [
    {
      "id": "wedding-20240810T143045-r5a-0",
      "timestamp": "2024-08-10T14:30:45+02:00",
      "camera": "Canon EOS R5",
      "urls": {
        "full": "photos/full/wedding-20240810T143045-r5a-0.jpg",
        "web": "photos/web/wedding-20240810T143045-r5a-0.jpg",
        "thumb": "photos/thumb/wedding-20240810T143045-r5a-0.webp"
      }
    }
  ]
}
```

### Implementation Tasks

1. **Photo Processing Enhancement**
   - [ ] Add file hash calculation for change detection
   - [ ] Generate `prod/gallery-metadata.json` with corrected timestamps
   - [ ] Include original EXIF data and corrections in metadata
   - [ ] Update tests for JSON metadata generation

2. **Build System Updates**
   - [ ] Modify `PhotoMetadataService` to read from JSON metadata
   - [ ] Generate frontend-optimized `gallery-data.json`
   - [ ] Maintain backward compatibility with filename parsing
   - [ ] Update template rendering to use JSON data

3. **Idempotent Deployment System**
   - [ ] Download remote `gallery-metadata.json` from S3 bucket
   - [ ] Compare local vs remote metadata (file hashes, timestamps)
   - [ ] Generate deployment plan (add/update/delete operations)
   - [ ] Selective upload only changed files
   - [ ] Upload updated metadata files

4. **Deployment EXIF Modification** ⚠️ **CRITICAL REQUIREMENT**
   - [ ] **Create temporary copies** of photos during deployment
   - [ ] **Modify EXIF data in copies** (apply DateTimeOriginal offset, set OffsetTimeOriginal to +02:00)
   - [ ] **Upload corrected copies to S3** (not originals)
   - [ ] **Preserve originals completely unchanged** for archive/CI purposes
   - [ ] Use piexif or similar library for EXIF writing
   - [ ] Test EXIF modification preserves image quality

5. **Deployment Optimization**
   - [ ] Skip unchanged photos based on hash comparison
   - [ ] Batch operations for efficiency
   - [ ] Progress reporting for large deployments
   - [ ] Rollback capability for failed deployments

## Real-world Deployment Testing **[FUTURE PRIORITY]**

**Objective**: Set up and test production S3/Hetzner bucket with CDN integration.

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

