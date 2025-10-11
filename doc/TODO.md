# Galleria - Development Specification

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

The project follows a clear command pipeline for processing and deploying photos:

```txt
Original Photos (PIC_SOURCE_PATH_FULL)
    ↓ [process-photos]
Processed Photos (PROCESSED_DIR)
    ↓ [upload-photos]
S3 Public Bucket
    ↓ [build]
Static Site (OUTPUT_DIR)
    ↓ [deploy]
Live Website
```

#### Command Overview

1. **`process-photos`** - Photo processing pipeline
   - Reads original photos from `PIC_SOURCE_PATH_FULL`
   - Extracts EXIF data and generates chronological filenames
   - Creates web-sized versions (2048x2048 max JPEG)
   - Creates thumbnails (400x400 WebP)
   - Outputs to `PROCESSED_DIR` with structure:
     ```
     processed-photos/
       full/     (symlinks with chronological names)
       web/      (resized JPEGs for web viewing)
       thumb/    (WebP thumbnails for gallery grid)
     ```

2. **`upload-photos`** - S3 upload for processed photos
   - Uploads from `PROCESSED_DIR` to S3 public bucket
   - Preserves directory structure (full/web/thumb)
   - Skips already uploaded files (idempotent)
   - Supports dry-run and progress tracking

3. **`build`** - Static site generation
   - Generates JSON metadata from processed photos
   - Creates static HTML using Jinja2 templates
   - Copies static assets (CSS/JS)
   - Outputs complete site to `OUTPUT_DIR`

4. **`deploy`** - Site deployment
   - Uploads static site from `OUTPUT_DIR` to hosting
   - Can target S3 static website hosting or other platforms
   - Handles CDN cache invalidation if needed

#### Usage Patterns

```bash
# Full pipeline for new photos
python manage.py process-photos
python manage.py upload-photos --progress
python manage.py build
python manage.py deploy

# Development workflow (skip S3 upload)
python manage.py process-photos --source ./test-photos
python manage.py build --skip-s3
python manage.py deploy --dry-run

# Update only the site (photos already processed)
python manage.py build
python manage.py deploy
```

**Note**: Each command can be run independently for testing and development. The commands are designed to be idempotent - running them multiple times is safe.

---

## Important Reminders

- Do what has been asked; nothing more, nothing less
- NEVER create files unless they're absolutely necessary for achieving your goal
- ALWAYS prefer editing an existing file to creating a new one
- NEVER proactively create documentation files (*.md) or
  README files unless explicitly requested

## Development Guidelines

### Commit Message Format

- Title: Maximum 50 characters including prefix
- Body: Maximum 72 characters per line
- Body text should use '-' bullets with proper nesting
- Use prefixes:
  - `Tst:` for test-related changes
  - `Fix:` for bug fixes
  - `Ft:` for new features
  - `Ref:` for refactoring
  - `Doc:` for documentation
  - `Pln:` for planning/TODO updates
- No signature block - do not include emoji, links, or Co-Authored-By lines

### Testing Requirements

- **Test Command**: Use `uv run pytest` to run tests (NOT `python -m pytest`)
- **Specific Test Files**: Use `uv run pytest test/test_filename.py -v` for focused testing
- ALWAYS run tests before suggesting a commit
- Follow E2E + TDD approach:
  - E2E tests find larger missing or broken pieces
  - TDD fills or fixes those pieces incrementally
- TDD/E2E workflow:
  - Build tests singularly first
  - Ensure test fails as expected (red)
  - Implement change to make test pass (green)
  - Consider refactors for better solution (refactor)
  - Move to next test when complete
- Task management:
  - Each test typically corresponds to a TODO task
  - Some tasks require multiple tests
  - After test(s) pass and refactors complete: update TODO.md, git commit
- Implement in small steps with clear logical breaks:
  - Add one test case or feature at a time
  - Test immediately after each testable addition
  - Never write massive amounts of code without testing

### Code Style

- Follow existing patterns in the codebase
- Check neighboring files for conventions
- Never assume a library is available - verify in package.json/requirements
- Don't add comments unless explicitly asked
- Match indentation and formatting of existing code
- Follow PEP 8, ruff and typical Python conventions:
  - No trailing whitespace
  - Blank line at end of file
  - Two blank lines between top-level definitions
  - One blank line between method definitions
  - Spaces around operators and after commas
  - No unnecessary blank lines within functions
  - Maximum line length of 88 characters (Black/Ruff default)

### Project-Specific Instructions

- This is a custom static site generator based gallery named "Galleria"
- Supports preprocessing copies of a specific wedding photo collection
- Current focus areas are tracked in TODO.md
- Keep TODO.md updated:
  - Update "Current Tasks" section when starting/stopping work
  - Mark completed items with [x]
  - Add new tasks as they're discovered
  - Document progress for easy resumption
- Keep `./doc` updated
  - `doc/README.md`
    - The overview and index to other documentation documents
  - The rest are named after key documentation areas

## Development Tasks & Specifications



### Settings Architecture & Command Infrastructure

**Deliverable**: Django-style settings hierarchy with command system

#### Acceptance Criteria

- [x] Command infrastructure with manage.py entry point
- [x] find-samples command implemented with all edge case detection
- [x] Settings hierarchy with TEST_OUTPUT_PATH for separating test results from production paths

#### Settings Architecture

```python
# Directory hierarchy with XDG compliance (XDG overrides project defaults)
CONFIG_DIR = BASE_DIR  # Default: project root, override: ~/.config/galleria
CACHE_DIR = BASE_DIR / 'cache'  # Default: ./cache, override: ~/.cache/galleria

# Local settings: project_root/settings.local.py (default)
LOCAL_SETTINGS_FILENAME = os.getenv('GALLERIA_LOCAL_SETTINGS_FILENAME', 'settings.local.py')
LOCAL_SETTINGS_PATH = CONFIG_DIR / LOCAL_SETTINGS_FILENAME

# Photo paths: ./pics (default fallback), production uses XDG data directories
PIC_SOURCE_PATH_FULL = Path(os.getenv('GALLERIA_PIC_SOURCE_PATH_FULL', 
                                      str(BASE_DIR / 'pics')))

# Test output paths: Keep test results separate from production processing
TEST_OUTPUT_PATH = Path(os.getenv('GALLERIA_TEST_OUTPUT_PATH', 
                                  str(CACHE_DIR / 'test-output')))
```

#### Command Structure

- manage.py - Click-based command entry point
- src/command/find_samples.py - Scan photos, detect edge cases, extract EXIF, save to JSON

##### find-samples Command Requirements
**Purpose**: Identify sample photos for testing the processing pipeline

**Edge Cases to Detect**:
- Burst mode sequences (photos with identical/near-identical timestamps)
- Missing or corrupted EXIF data
- Timestamp conflicts (same timestamp from different cameras)
- Camera variety (different manufacturers, filename patterns)
- Timezone differences (using GPS data)
- Filename edge cases (rollovers, special characters, user-renamed)

**CLI Options**:
- `--pic-source-path-full`, `--pic-source`, `-s`: Directory to scan (overrides settings)
- `--generate-dummy-samples`: Create synthetic test images for missing edge cases
- `--sample-types`: Comma-separated list of edge cases to detect (default: all)
- `--output-format`: Output format - json, text (default: json)
- `--cache-file`: Override default JSON file location (default: CACHE_DIR/samples.json)

**Output Structure** (saved to JSON):
```python
{
    'photos': [
        {
            'path': Path,
            'exif': dict,  # Extracted EXIF data
            'edge_cases': ['burst', 'missing_exif'],  # Detected issues
            'camera': str,  # Camera model/manufacturer
            'timestamp': datetime,
            'gps': tuple,  # (lat, lon) if available
        }
    ],
    'summary': {
        'total_photos': int,
        'edge_case_counts': {'burst': 5, 'missing_exif': 2, ...},
        'cameras': {'Canon EOS 5D': 10, 'iPhone 12': 5, ...},
    }
}
```

#### Test Coverage Required

- Settings import hierarchy (default, local override, env override, CLI override)
- XDG cache directory resolution
- Command option parsing and settings integration
- Edge case detection logic (burst, missing EXIF, timestamp conflicts)
- EXIF extraction functionality
- JSON file save/load operations
- Dummy sample generation

---



### Remote Storage Integration (S3-Compatible)

**Deliverable**: S3-compatible object storage for both archive and production photos

#### Architecture Overview

**Dual-Bucket Strategy**:
- **Private Archive Bucket**: Store original photos for safe-keeping (authenticated access only) - initially via manual upload
- **Public Gallery Bucket**: Store processed photos for public gallery access (via CDN)

#### Acceptance Criteria

- [ ] Generic S3-compatible implementation using boto3 (supports Hetzner, AWS, DigitalOcean, etc.)
- [ ] Upload processed photos to public gallery bucket with validation
- [ ] Handle API errors gracefully with retry logic
- [ ] Support batch operations for 30GB+ photo collections
- [ ] Documentation for bucket setup with security best practices
- [ ] S3 configuration with proper settings precedence

#### Configuration Required

**Settings Precedence**: All S3 settings follow standard hierarchy:
`settings.py (defaults) → settings.local.py → GALLERIA_* env vars → CLI args`

**Note**: Only environment variables use the `GALLERIA_` prefix (host-level scope)

```python
# Private archive bucket (for original photos)
S3_ARCHIVE_ENDPOINT = os.getenv('GALLERIA_S3_ARCHIVE_ENDPOINT')
S3_ARCHIVE_ACCESS_KEY = os.getenv('GALLERIA_S3_ARCHIVE_ACCESS_KEY')
S3_ARCHIVE_SECRET_KEY = os.getenv('GALLERIA_S3_ARCHIVE_SECRET_KEY')
S3_ARCHIVE_BUCKET = os.getenv('GALLERIA_S3_ARCHIVE_BUCKET', 'galleria-originals-private')
S3_ARCHIVE_REGION = os.getenv('GALLERIA_S3_ARCHIVE_REGION', 'us-east-1')

# Public gallery bucket (for processed photos)  
S3_PUBLIC_ENDPOINT = os.getenv('GALLERIA_S3_PUBLIC_ENDPOINT')
S3_PUBLIC_ACCESS_KEY = os.getenv('GALLERIA_S3_PUBLIC_ACCESS_KEY')
S3_PUBLIC_SECRET_KEY = os.getenv('GALLERIA_S3_PUBLIC_SECRET_KEY')
S3_PUBLIC_BUCKET = os.getenv('GALLERIA_S3_PUBLIC_BUCKET', 'galleria-wedding-public')
S3_PUBLIC_REGION = os.getenv('GALLERIA_S3_PUBLIC_REGION', 'us-east-1')
```

#### Upload to Public Gallery Bucket

**Command**: `python manage.py upload-photos`

```bash
# Upload processed photos to public bucket
python manage.py upload-photos

# Custom output directory with dry-run
python manage.py upload-photos --source ./processed-photos --dry-run

# Show progress bar
python manage.py upload-photos --progress
```

**Requirements**:
- Upload processed photos (full/web/thumb) to public bucket
- Maintain chronological filename structure
- Skip already uploaded files (idempotent)
- Validate S3 configuration before upload
- Generate SHA256 checksums for integrity
- Support resumable uploads for large files

#### Service Functions Required

```python
# src/services/s3_storage.py
def get_s3_client(endpoint, access_key, secret_key, region='us-east-1'):
    """Create boto3 S3 client for any S3-compatible service"""
    
def upload_file_to_s3(client, local_path, bucket, key, progress_callback=None):
    """Upload single file with progress tracking"""
    
def upload_directory_to_s3(client, local_dir, bucket, prefix='', dry_run=False):
    """Upload entire directory preserving structure"""
    
def list_bucket_files(client, bucket, prefix=''):
    """List all files in bucket with given prefix"""
    
def file_exists_in_s3(client, bucket, key):
    """Check if file already exists in bucket"""

# Future async operations (requires aioboto3)
async def process_photos_streaming(source_bucket, dest_bucket):
    """Stream photos from archive -> process -> upload to gallery"""
```

#### Documentation Requirements

- **doc/remote-storage-setup.md**: Step-by-step guide including:
  - Hetzner Object Storage account setup
  - Creating private archive bucket with restricted access
  - Creating public gallery bucket with public read access
  - Manual upload instructions for private archive bucket
  - Environment variable configuration and precedence
  - Security best practices (IAM policies, CORS settings)
  - CDN integration overview (detailed setup: TODO: `doc/bunnycdn-setup.md`)
  - Example configurations for AWS S3, DigitalOcean Spaces

#### Testing Strategy

- Mock S3 operations using moto library
- Test upload resumption after interruption
- Validate checksum verification
- Test error handling and retry logic
- Integration tests with actual S3-compatible service

#### Next Implementation Steps

**IMPORTANT**: Before implementing upload-photos command, plan the real-world test strategy:

- **Test Planning Required**: Design comprehensive real-world test approach
- **Observation Strategy**: What metrics/behaviors to monitor during upload
- **Error Scenarios**: How to handle and recover from partial uploads
- **Performance Monitoring**: Upload speed, memory usage, network behavior
- **Verification Method**: How to confirm all files uploaded correctly
- **Test Data Selection**: Which subset of photos to use for initial testing

**Goal**: Minimize number of real-world test runs due to time/bandwidth costs

#### Future Planning Needed

- **Public Bucket Organization**: Directory structure for processed photos (full/web/thumb)
- **Metadata Sync**: Keeping local JSON cache in sync with remote storage

---

### Static Site Generation

**Deliverable**: Custom HTML generation with Jinja2 templates

#### Acceptance Criteria

- [ ] Custom Jinja2 templates with Tailwind CSS + AlpineJS
- [ ] Gallery page template with photo grid
- [ ] JSON API endpoints from cached photo data for AlpineJS frontend
- [ ] Basic navbar and site structure
- [ ] SEO configuration with noindex
- [ ] Mobile-responsive design

#### Template Structure Required

```
templates/
-> base.j2.html             (Tailwind + AlpineJS setup)
-> gallery.j2.html          (Photo grid template)
-> index.j2.html            (Landing page)
-> navbar.j2.html           (Navigation component)

static/
-> css/
-> js/
   -> gallery.js            (AlpineJS gallery logic)
-> img/                     (Site assets - logos, icons)
```

#### Site Generation Configuration

```python
# Custom site generator settings
TEMPLATE_DIR = 'templates/'
STATIC_DIR = 'static/'
OUTPUT_DIR = 'output/'

# Template configuration
TEMPLATES = {
    'index.j2.html': 'index.html',
    'gallery.j2.html': 'gallery.html',
}

# Generate JSON API responses from cached photo metadata
PHOTO_METADATA_SOURCE = 'json'  # Photo data served from JSON cache
STATIC_PATHS = ['css', 'js', 'img']
```

#### Gallery Template Requirements

- Thumbnail grid with infinite scroll
- Checkbox selection for photos
- Download buttons (web/full resolution)
- Select all/none functionality
- AlpineJS state management

---

### Frontend Functionality

**Deliverable**: Interactive photo gallery with AlpineJS

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

---

### BunnyCDN Configuration

**Deliverable**: CDN setup for global content delivery

#### Acceptance Criteria

- [ ] BunnyCDN pull zone configured with Hetzner as origin
- [ ] Proper caching headers set
- [ ] CDN URLs integrated into static site
- [ ] Performance testing confirms global speed improvement
- [ ] Create doc/bunnycdn-setup.md with detailed configuration steps
- [ ] Update doc/remote-storage-setup.md to link to CDN documentation

#### CDN Configuration Required

```
Origin URL: https://your-bucket.hetzner-endpoint.com
Pull Zone: galleria-cdn
Caching: Standard settings for images
Purge: Manual trigger capability
```

---

### Build & Deployment Pipeline

**Deliverable**: Automated build and deployment scripts

#### Acceptance Criteria

- [ ] Build script processes all photos correctly
- [ ] Custom site generator creates static HTML successfully
- [ ] Deployment script uploads to Hetzner
- [ ] Non-obvious URL structure implemented
- [ ] Full pipeline runs without manual intervention

#### Command Implementation Requirements

##### process-photos Command

**Purpose**: Process original photos into web-ready formats

**CLI Options**:
- `--source`, `-s`: Override PIC_SOURCE_PATH_FULL
- `--output`, `-o`: Override PROCESSED_DIR
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

**Purpose**: Deploy static site to production hosting

**CLI Options**:
- `--source`, `-s`: Override OUTPUT_DIR
- `--target`: Deployment target (s3-static, netlify, etc.)
- `--dry-run`: Show deployment plan without executing
- `--invalidate-cdn`: Trigger CDN cache purge

**Deployment Steps**:
1. Validate deployment configuration
2. Upload static files to hosting target
3. Update DNS/CDN configuration if needed
4. Verify deployment with smoke tests
5. Output production URLs

---

### Testing & Quality Assurance

**Deliverable**: Comprehensive test suite and manual testing

#### Acceptance Criteria

- [ ] All unit tests passing (90%+ coverage for core logic)
- [ ] Integration tests for Hetzner API
- [ ] Cross-browser testing (Chrome, Safari, Firefox)
- [ ] Mobile device testing
- [ ] Performance testing under load
- [ ] User acceptance testing with family members

#### Test Categories Required

```
tests/
-> test_exif_processing.py
-> test_filename_generation.py
-> test_file_operations.py
-> test_hetzner_integration.py
-> test_static_generation.py
-> test_frontend_functionality.py
```

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

