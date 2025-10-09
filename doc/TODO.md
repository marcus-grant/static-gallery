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
- **Private Archive Bucket**: Store original photos for safe-keeping (authenticated access only)
- **Public Gallery Bucket**: Store processed photos for public gallery access (via CDN)

#### Acceptance Criteria

- [ ] Generic S3-compatible implementation using boto3 (supports Hetzner, AWS, DigitalOcean, etc.)
- [ ] Upload original photos to private archive bucket with `upload-originals` command
- [ ] Preserve original directory structure and filenames in archive
- [ ] Progress reporting and dry-run option for large collections
- [ ] Upload processed photos to public gallery bucket
- [ ] Handle API errors gracefully with retry logic
- [ ] Support batch operations for 30GB+ photo collections
- [ ] Documentation for bucket setup with security best practices

#### Configuration Required

```python
# Private archive bucket (for original photos)
GALLERIA_S3_ARCHIVE_ENDPOINT = os.getenv('GALLERIA_S3_ARCHIVE_ENDPOINT')
GALLERIA_S3_ARCHIVE_ACCESS_KEY = os.getenv('GALLERIA_S3_ARCHIVE_ACCESS_KEY')
GALLERIA_S3_ARCHIVE_SECRET_KEY = os.getenv('GALLERIA_S3_ARCHIVE_SECRET_KEY')
GALLERIA_S3_ARCHIVE_BUCKET = os.getenv('GALLERIA_S3_ARCHIVE_BUCKET', 'galleria-originals-private')
GALLERIA_S3_ARCHIVE_REGION = os.getenv('GALLERIA_S3_ARCHIVE_REGION', 'us-east-1')

# Public gallery bucket (for processed photos)  
GALLERIA_S3_PUBLIC_ENDPOINT = os.getenv('GALLERIA_S3_PUBLIC_ENDPOINT')
GALLERIA_S3_PUBLIC_ACCESS_KEY = os.getenv('GALLERIA_S3_PUBLIC_ACCESS_KEY')
GALLERIA_S3_PUBLIC_SECRET_KEY = os.getenv('GALLERIA_S3_PUBLIC_SECRET_KEY')
GALLERIA_S3_PUBLIC_BUCKET = os.getenv('GALLERIA_S3_PUBLIC_BUCKET', 'galleria-wedding-public')
GALLERIA_S3_PUBLIC_REGION = os.getenv('GALLERIA_S3_PUBLIC_REGION', 'us-east-1')
```

#### Original Photo Archive Upload

**Command**: `python manage.py upload-originals`

```bash
# Upload from settings.local.py path
python manage.py upload-originals

# Custom source with dry-run
python manage.py upload-originals --source /path/to/photos --dry-run

# Show progress bar
python manage.py upload-originals --progress
```

**Requirements**:
- Upload all photos from `PIC_SOURCE_PATH_FULL` (default: settings.local.py)
- Maintain original directory structure in bucket
- Skip already uploaded files (idempotent)
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
  - Generating read-only access keys for private bucket
  - Security best practices (IAM policies, CORS settings)
  - Example configurations for AWS S3, DigitalOcean Spaces

#### Testing Strategy

- Mock S3 operations using moto library
- Test upload resumption after interruption
- Validate checksum verification
- Test error handling and retry logic
- Integration tests with actual S3-compatible service

#### Future Planning Needed

- **Async Photo Pipeline**: Details for streaming process (download → process → upload)
- **Public Bucket Organization**: Directory structure for processed photos (full/web/thumb)
- **CDN Integration**: How public bucket connects to BunnyCDN
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

#### Build Script (build.py) Requirements

```python
def main():
    # 1. Process photos (EXIF -> Chronological Filenames -> thumbnails)
    # 2. Upload to Hetzner public bucket
    # 3. Generate JSON metadata for gallery
    # 4. Run custom HTML generation
    # 5. Prepare for deployment
```

#### Deployment Script (deploy.py) Requirements

```python
def main():
    # 1. Upload static site to Hetzner
    # 2. Configure CDN if needed
    # 3. Verify deployment
    # 4. Output final URLs
```

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

