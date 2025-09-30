# Galleria - Development Specification

## Project Overview

A static photo gallery built with a custom Python static site generator,
using AlpineJS for frontend interactions and
Tailwind CSS for styling.
Photos are processed with UUIDv7-based filenames derived from EXIF data and
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
Photographer's Photos -> EXIF Extraction -> UUID Generation ->
-> Thumbnail Creation -> Upload to Buckets ->
-> Custom HTML Generation -> Deploy
```

### Photo Organization Structure

```txt
Private Bucket (Hetzner):     Public Bucket (Hetzner):        Static Site:
/originals/                   /galleria-wedding/              Gallery page with:
  IMG_001.jpg                   {uuid}.jpg  (full)             - Thumbnail grid
  IMG_002.jpg                   {uuid}.jpg  (web)              - Infinite scroll
  ...                           {uuid}.webp (thumb)            - Multi-select downloads
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

### Data Models & Database Architecture

**Deliverable**: SQLAlchemy 2.0 models with SQLite backend for photo metadata

#### Development Approach

1. **TDD develop model classes** - Photo, EXIF data models
2. **Database setup with async** - SQLAlchemy 2.0 + aiosqlite
3. **Migration system** - Alembic for schema changes
4. **Integration testing** - Async database operations

#### Acceptance Criteria

- [ ] `src/models/photo.py` - Photo model with SQLAlchemy 2.0
- [ ] `src/models/database.py` - Database connection and session management
- [ ] Async database operations with aiosqlite
- [ ] Alembic migration setup for schema management
- [ ] Unit tests for model operations
- [ ] JSON serialization for API responses

#### Required Models

```python
# src/models/photo.py
class Photo(Base):
    """Photo model with EXIF and filesystem metadata"""
    id: Mapped[int] = mapped_column(primary_key=True)
    path: Mapped[str] = mapped_column(String(512), unique=True)
    filename: Mapped[str] = mapped_column(String(255))
    file_size: Mapped[int]
    created_at: Mapped[datetime]
    
class ExifData(Base):
    """EXIF metadata extracted from photos"""
    id: Mapped[int] = mapped_column(primary_key=True)
    photo_id: Mapped[int] = mapped_column(ForeignKey("photo.id"))
    camera_make: Mapped[Optional[str]]
    camera_model: Mapped[Optional[str]]
    timestamp: Mapped[Optional[datetime]]
    gps_latitude: Mapped[Optional[float]]
    gps_longitude: Mapped[Optional[float]]
```

#### Database Features

- **SQLite for development/production** - Single file, no server required
- **Async operations** - Non-blocking database calls
- **JSON API serialization** - Models convert to dict for FastAPI responses
- **Query optimization** - Efficient edge case detection with SQL
- **Migration support** - Schema evolution with Alembic

### Project Bootstrap & Sample Data

**Deliverable**: Working development environment with test photos

#### Acceptance Criteria

- [ ] Git repository initialized with proper structure
- [ ] Python 3.12 virtual environment configured
- [ ] Project dependencies installed and documented
- [ ] Sample photo collection identified and organized
- [ ] Basic project documentation complete

#### File Structure Required

```
galleria/
|-- README.md
|-- requirements.txt
|-- .gitignore
|-- src/
|   |-- command/       (Click commands - view layer)
|   |-- model/         (SQLAlchemy 2.0 data models with SQLite backing)
|   |-- services/      (Business logic)
|   `-- utils/         (Utility modules)
|-- templates/         (Jinja2 templates - .j2.html extensions)
|-- static/            (CSS, JS, img assets)
|-- output/            (Generated static site)
|-- tests/
|-- sample-photos/
|   |-- full/          (original resolution test photos)
|   |-- web/           (web-optimized test photos)
|   `-- burst/         (burst mode sequence examples)
|-- settings.py
|-- build.py
`-- deploy.py
```

#### Sample Photo Requirements

- **Burst mode sequences**: 3-5 photos taken in rapid succession
- **Multiple cameras**: Photos from different camera models/brands
- **EXIF variety**: Photos with/without subsecond data, GPS coordinates
- **Location diversity**: Photos representing different wedding venues
- **Edge cases**: Missing EXIF data, corrupted timestamps

#### Dependencies (requirements.txt)

```
jinja2>=3.1.0
Pillow>=10.0.0
exifread>=3.0.0
python-dotenv>=1.0.0
boto3>=1.26.0  # for S3-compatible Hetzner API
sqlalchemy>=2.0.0  # SQLAlchemy 2.0 with async support
aiosqlite>=0.17.0  # Async SQLite driver
alembic>=1.13.0  # Database migrations
pytest>=7.0.0
pytest-asyncio>=0.21.0  # For async tests
```

---

### Settings Architecture & Command Infrastructure

**Deliverable**: Django-style settings hierarchy with command system

#### Acceptance Criteria

- [ ] Command infrastructure with manage.py entry point
- [ ] find-samples and list-samples commands implemented

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
```

#### Command Structure

- manage.py - Click-based command entry point
- src/command/find_samples.py - Scan photos, detect edge cases, extract EXIF, save to JSON
- src/command/list_samples.py - Display saved metadata from JSON

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

### EXIF Service Module

**Deliverable**: EXIF data extraction and edge case detection service

#### Camera Burst Mode Research Summary

Based on research, cameras handle burst mode in two ways:
- **With subsecond EXIF** (Canon/Nikon): SubsecTimeOriginal provides ~10ms precision 
- **Without subsecond EXIF** (Sony/older cameras): Multiple photos share same 1-second timestamp

**Detection Strategy**: Sort by EXIF timestamp + subsecond (if available), fall back to filename sequence for identical timestamps, detect bursts within ~200ms intervals.

#### Development Approach (TDD Order)

1. **Core EXIF extraction helpers** - Basic timestamp and camera info extraction
2. **Timestamp utilities** - Subsecond handling and chronological sorting  
3. **Burst detection algorithms** - Handle both subsecond and filename fallback cases
4. **Edge case detection** - Conflicts, missing EXIF, camera diversity
5. **Integration with find_samples** - Filter interesting photos for testing

#### Acceptance Criteria

- [x] Core EXIF extraction functions (extract_exif_data, get_datetime_taken, get_camera_info)
- [x] Subsecond timestamp handling (get_subsecond_precision)
- [x] Timestamp utilities (combine_datetime_subsecond, has_subsecond_precision)
- [x] Chronological photo sorting with camera/filename fallback
- [ ] Burst sequence detection for both subsecond and non-subsecond cameras
- [ ] Edge case helpers (timestamp conflicts, missing EXIF, camera diversity)
- [ ] Integration with find_samples command for photo filtering
- [x] Unit tests with sample photos from different camera manufacturers

#### Required Helper Functions (Development Order)

```python
# Phase 1: Core EXIF extraction
def extract_exif_data(photo_path: Path) -> dict:
    """Extract raw EXIF metadata from photo file"""
    
def get_datetime_taken(exif_data: dict) -> Optional[datetime]:
    """Parse DateTimeOriginal EXIF tag"""
    
def get_subsecond_precision(exif_data: dict) -> Optional[int]:
    """Parse SubsecTimeOriginal for burst mode precision"""
    
def get_camera_info(exif_data: dict) -> dict:
    """Extract camera make, model, etc."""

# Phase 2: Timestamp utilities  
def combine_datetime_subsecond(dt: datetime, subsec: Optional[int]) -> datetime:
    """Combine datetime with subsecond precision for accurate sorting"""
    
def has_subsecond_precision(exif_data: dict) -> bool:
    """Check if camera supports subsecond timestamps"""

# Phase 3: Chronological sorting
def sort_photos_chronologically(photos: List[Path]) -> List[Tuple[Path, datetime, dict]]:
    """Sort photos by timestamp + camera/filename fallback for identical times"""

# Phase 4: Burst detection
def detect_burst_sequences(sorted_photos: List[Tuple[Path, datetime, dict]]) -> List[List[Path]]:
    """Group photos taken in rapid succession (within ~200ms)"""
    
def is_burst_candidate(photo1: Path, photo2: Path, max_interval_ms: int = 200) -> bool:
    """Check if two photos are part of same burst sequence"""

# Phase 5: Edge case detection
def find_timestamp_conflicts(photos: List[Path]) -> List[List[Path]]:
    """Find photos with same timestamp from different cameras"""
    
def find_missing_exif_photos(photos: List[Path]) -> List[Path]:
    """Find photos without critical EXIF data"""
    
def get_camera_diversity_samples(photos: List[Path]) -> dict:
    """Group photos by camera make/model for diversity testing"""
```

#### Edge Cases to Handle

- **Burst mode sequences** - Photos with identical/near-identical timestamps
- **Missing EXIF data** - Corrupted or stripped metadata
- **Timestamp conflicts** - Same timestamp from different cameras (common at events with multiple photographers)
- **Camera variety** - Different manufacturers, EXIF formats
- **GPS data extraction** - Location information when available
- **Subsecond precision** - High-speed shooting timestamp resolution

#### Test Coverage Required

- EXIF extraction from various camera formats (Canon, Nikon, iPhone, etc.)
- Burst sequence detection with different time intervals
- Missing/corrupted EXIF handling
- Database integration with async operations
- Performance testing with large photo sets

---

### EXIF Processing & UUID Generation

**Deliverable**: Core logic for reading photo metadata and generating UUIDs

#### Acceptance Criteria

- [ ] Extract EXIF timestamp, GPS, camera model from photos
- [ ] Generate UUIDv7 with EXIF timestamp as time component
- [ ] Encode UUIDs as Base32 for shorter filenames
- [ ] Handle burst mode with subsecond or filename sequence
- [ ] Maintain k-sortability (chronological ordering)
- [ ] All core logic unit tests passing

#### Core Functions Required

```python
def extract_exif_data(photo_path) -> dict:
    """Extract timestamp, GPS, camera info from photo"""
    
def generate_uuid_from_exif(exif_data, original_filename) -> str:
    """Create UUIDv7 from EXIF data, encode as Base32"""
    
def handle_burst_sequence(photo_list) -> list:
    """Ensure proper ordering for burst mode photos"""
```

#### Test Coverage Required

- EXIF extraction from various camera formats
- UUID generation produces k-sortable results
- Burst mode sequence preservation
- Collision handling for identical timestamps
- Base32 encoding/decoding correctness

---

### File Processing Pipeline

**Deliverable**: System to rename photos and generate thumbnails

#### Acceptance Criteria

- [ ] Rename photos using UUID system
- [ ] Generate WebP thumbnails from web-optimized photos
- [ ] Maintain file associations (full/web/thumb with same UUID)
- [ ] Handle file operations safely with error handling
- [ ] Process photos in chronological order

#### Processing Functions Required

```python
def rename_photo_with_uuid(original_path, uuid_filename) -> str:
    """Rename photo file with UUID filename"""
    
def create_thumbnail(web_photo_path, output_path) -> bool:
    """Generate WebP thumbnail from web photo"""
    
def process_photo_collection(source_dirs) -> dict:
    """Process all photos and return metadata"""
```

#### Output Structure

```
wedding-pics/
|-- full/
|   |-- ABC123DEF456GHI789.jpg
|   `-- DEF456GHI789JKL012.jpg
|-- web/
|   |-- ABC123DEF456GHI789.jpg
|   `-- DEF456GHI789JKL012.jpg
`-- thumb/
    |-- ABC123DEF456GHI789.webp
    `-- DEF456GHI789JKL012.webp
```

---

### Hetzner Integration

**Deliverable**: Upload/download functionality for Hetzner object storage

#### Acceptance Criteria

- [ ] Authenticate to both private and public Hetzner buckets
- [ ] Upload processed photos to public bucket
- [ ] Read original photos from private bucket (if configured)
- [ ] Handle API errors gracefully
- [ ] Support batch operations for large photo sets

#### Configuration Required

```python
# Environment variables
HETZNER_PRIVATE_ACCESS_KEY=
HETZNER_PRIVATE_SECRET_KEY=
HETZNER_PRIVATE_BUCKET=
HETZNER_PUBLIC_ACCESS_KEY=
HETZNER_PUBLIC_SECRET_KEY=
HETZNER_PUBLIC_BUCKET=
HETZNER_ENDPOINT=
```

#### Integration Functions Required

```python
def upload_to_hetzner(file_path, bucket, key) -> bool:
    """Upload file to Hetzner bucket"""
    
def download_from_hetzner(bucket, key, local_path) -> bool:
    """Download file from Hetzner bucket"""
    
def batch_upload_photos(photo_metadata, bucket) -> dict:
    """Upload all processed photos with progress tracking"""
```

---

### Static Site Generation

**Deliverable**: Custom HTML generation with Jinja2 templates

#### Acceptance Criteria

- [ ] Custom Jinja2 templates with Tailwind CSS + AlpineJS
- [ ] Gallery page template with photo grid
- [ ] JSON API endpoints from SQLite data for AlpineJS frontend
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

# Generate JSON API responses from SQLite database
PHOTO_METADATA_SOURCE = 'sqlite'  # Photo data served from database
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
    # 1. Process photos (EXIF -> UUID -> thumbnails)
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
-> test_uuid_generation.py
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

## TinyID Analysis

### TinyID vs UUIDv7 Comparison

**TinyID Characteristics:**

- Shorter IDs (typically 11-14 characters)
- Timestamp-based with customizable encoding
- Built-in collision resistance
- Good for URL-friendly IDs

**UUIDv7 + Base32 Approach (Selected):**

- 26 characters (vs 36 hex chars with hyphens)
- Easy incorporation of multiple EXIF data points
- Standard UUID format with timestamp ordering
- Better control over data incorporation

**Decision Rationale:**
UUIDv7 + Base32 chosen for easier integration of multiple EXIF fields (timestamp, camera, GPS, filename) while maintaining k-sortability and reasonable length.

---

*This specification prioritizes rapid deployment of core functionality. Features marked as "Future" can be implemented in subsequent iterations after the initial gallery is live and functional.*

