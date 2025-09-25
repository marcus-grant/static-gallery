# Galleria - Development Specification

## Project Overview

A static wedding photo gallery built with Pelican, using AlpineJS for frontend interactions and Tailwind CSS for styling. Photos are processed with UUIDv7-based filenames derived from EXIF data and hosted on Hetzner object storage with BunnyCDN for global distribution.

**Priority**: Speed of development and deployment over feature richness. Get a working, acceptable user experience deployed quickly.

## Stack & Workflow Overview

### Technology Stack
- **Static Site Generator**: Pelican (Python 3.12)
- **Frontend**: AlpineJS + Tailwind CSS (CDN, no build step)
- **Photo Processing**: Python with Pillow, exifread
- **Storage**: Hetzner object storage (private + public buckets)
- **CDN**: BunnyCDN with Hetzner as origin
- **Development**: Local build \u2192 Hetzner deployment

### Photo Processing Workflow
```
Photographer's Photos \u2192 EXIF Extraction \u2192 UUID Generation \u2192 
Thumbnail Creation \u2192 Upload to Buckets \u2192 Static Site Generation \u2192 Deploy
```

### Photo Organization Structure
```
Private Bucket (Hetzner):     Public Bucket (Hetzner):        Static Site:
/originals/                   /wedding-pics/                  Gallery page with:
  IMG_001.jpg                   {uuid}.jpg  (full)             - Thumbnail grid
  IMG_002.jpg                   {uuid}.jpg  (web)              - Infinite scroll
  ...                           {uuid}.webp (thumb)            - Multi-select downloads
```

### Storage Strategy
- **Private Hetzner Bucket**: Original photos with authentication (personal archive)
- **Public Hetzner Bucket**: Full + web + thumbnail versions (for static site)
- **BunnyCDN**: Global CDN caching content from public Hetzner bucket

---

## Development Tasks & Specifications

### Task 1: Project Bootstrap & Sample Data
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
\u251c\u2500\u2500 README.md
\u251c\u2500\u2500 requirements.txt
\u251c\u2500\u2500 .gitignore
\u251c\u2500\u2500 tests/
\u251c\u2500\u2500 content/
\u251c\u2500\u2500 themes/wedding/
\u251c\u2500\u2500 sample-photos/
\u2502   \u251c\u2500\u2500 full/          (original resolution test photos)
\u2502   \u251c\u2500\u2500 web/           (web-optimized test photos)
\u2502   \u2514\u2500\u2500 burst/         (burst mode sequence examples)
\u251c\u2500\u2500 build.py
\u2514\u2500\u2500 deploy.py
```

#### Sample Photo Requirements
- **Burst mode sequences**: 3-5 photos taken in rapid succession
- **Multiple cameras**: Photos from different camera models/brands
- **EXIF variety**: Photos with/without subsecond data, GPS coordinates
- **Location diversity**: Photos representing different wedding venues
- **Edge cases**: Missing EXIF data, corrupted timestamps

#### Dependencies (requirements.txt)
```
pelican>=4.8.0
Pillow>=10.0.0
exifread>=3.0.0
python-dotenv>=1.0.0
boto3>=1.26.0  # for S3-compatible Hetzner API
pytest>=7.0.0
```

---

### Task 2: Settings Architecture & Command Infrastructure
**Deliverable**: Django-style settings hierarchy with command system

#### Acceptance Criteria
- [ ] Settings hierarchy: CLI args > env vars > settings.local.py > settings.py
- [ ] Environment variables use GALLERIA_ prefix
- [ ] Local settings loaded from project root settings.local.py
- [ ] XDG-compliant cache directory with fallback to ./cache
- [ ] Command infrastructure with manage.py entry point
- [ ] find-samples and list-samples commands implemented
- [ ] Test coverage for settings precedence

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
- src/command/find_samples.py - Scan photos, extract EXIF, save to pickle
- src/command/list_samples.py - Display saved metadata

#### Test Coverage Required
- Settings import hierarchy (default, local override, env override, CLI override)
- XDG cache directory resolution
- Command option parsing and settings integration
- Pickle file save/load operations

---

### Task 3: EXIF Processing & UUID Generation
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

### Task 4: File Processing Pipeline
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
\u251c\u2500\u2500 full/
\u2502   \u251c\u2500\u2500 ABC123DEF456GHI789.jpg
\u2502   \u2514\u2500\u2500 DEF456GHI789JKL012.jpg
\u251c\u2500\u2500 web/
\u2502   \u251c\u2500\u2500 ABC123DEF456GHI789.jpg
\u2502   \u2514\u2500\u2500 DEF456GHI789JKL012.jpg
\u2514\u2500\u2500 thumb/
    \u251c\u2500\u2500 ABC123DEF456GHI789.webp
    \u2514\u2500\u2500 DEF456GHI789JKL012.webp
```

---

### Task 5: Hetzner Integration
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

### Task 6: Static Site Generation
**Deliverable**: Pelican configuration and custom theme

#### Acceptance Criteria
- [ ] Custom Pelican theme with Tailwind CSS + AlpineJS
- [ ] Gallery page template with photo grid
- [ ] JSON metadata generation for AlpineJS
- [ ] Basic navbar and site structure
- [ ] SEO configuration with noindex
- [ ] Mobile-responsive design

#### Theme Structure Required
```
themes/wedding/
\u251c\u2500\u2500 templates/
\u2502   \u251c\u2500\u2500 base.html           (Tailwind + AlpineJS setup)
\u2502   \u251c\u2500\u2500 gallery.html        (Photo grid template)
\u2502   \u251c\u2500\u2500 index.html          (Landing page)
\u2502   \u2514\u2500\u2500 navbar.html         (Navigation component)
\u251c\u2500\u2500 static/
\u2502   \u2514\u2500\u2500 js/
\u2502       \u2514\u2500\u2500 gallery.js      (AlpineJS gallery logic)
\u2514\u2500\u2500 theme.conf
```

#### Pelican Configuration (pelicanconf.py)
```python
THEME = 'themes/wedding'
STATIC_PATHS = ['photos', 'js']
TEMPLATE_PAGES = {
    'gallery.html': 'gallery.html',
}
# Generate JSON for AlpineJS
PHOTO_METADATA_JSON = True
```

#### Gallery Template Requirements
- Thumbnail grid with infinite scroll
- Checkbox selection for photos
- Download buttons (web/full resolution)
- Select all/none functionality
- AlpineJS state management

---

### Task 7: Frontend Functionality
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

### Task 8: BunnyCDN Configuration
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

### Task 9: Build & Deployment Pipeline
**Deliverable**: Automated build and deployment scripts

#### Acceptance Criteria
- [ ] Build script processes all photos correctly
- [ ] Pelican generates static site successfully
- [ ] Deployment script uploads to Hetzner
- [ ] Non-obvious URL structure implemented
- [ ] Full pipeline runs without manual intervention

#### Build Script (build.py) Requirements
```python
def main():
    # 1. Process photos (EXIF \u2192 UUID \u2192 thumbnails)
    # 2. Upload to Hetzner public bucket
    # 3. Generate JSON metadata for gallery
    # 4. Run Pelican static site generation
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

### Task 10: Testing & Quality Assurance
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
\u251c\u2500\u2500 test_exif_processing.py
\u251c\u2500\u2500 test_uuid_generation.py
\u251c\u2500\u2500 test_file_operations.py
\u251c\u2500\u2500 test_hetzner_integration.py
\u251c\u2500\u2500 test_static_generation.py
\u2514\u2500\u2500 test_frontend_functionality.py
```

---

### Task 10: Final Deployment & Monitoring
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