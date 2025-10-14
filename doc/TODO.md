# Galleria - Development Specification

**Commands implemented**: find-samples, upload-photos, process-photos

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
Processed Photos (PROCESSED_DIR)
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
   - Outputs to `PROCESSED_DIR` with structure:
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

### Static Site Generation

**Deliverable**: Custom HTML generation with Jinja2 templates **[NEXT]**

#### MVP Acceptance Criteria

- [x] Component-based Jinja2 templates with Tailwind CSS + AlpineJS (basic setup complete)
- [ ] Gallery page template with complete photo grid (all photos rendered server-side)
- [ ] Photo preview modal with navigation (click left/right 25% areas)
- [ ] Basic navbar and site structure
- [x] SEO configuration with noindex
- [ ] Mobile-responsive design
- [x] TDD approach with BeautifulSoup4 template testing

#### Template Structure Required

```
src/template/
-> base.j2.html             (Base layout with head, scripts)
-> gallery.j2.html          (Main gallery page extending base)
-> components/
   -> photo-grid.j2.html    (Grid container with ALL photos)
   -> photo-cell.j2.html    (Clickable photo thumbnail) [x]
   -> photo-modal.j2.html   (Photo preview modal with nav zones)
   -> navbar.j2.html        (Navigation component)

static/
-> js/
   -> gallery.js            (AlpineJS for modal + navigation)
-> css/
   -> custom.css            (Modal styles, navigation zones)
```

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

#### Development Server with Hot Reload

**Deliverable**: Local development server for template development **[IN PROGRESS]**

##### Requirements
- [x] Hot-reloading dev server that watches template files
- [x] Automatically rebuilds on template/CSS/JS changes  
- [x] Serves from prod/site/ directory
- [x] Root path (/) returns 404 without index.html
- [x] /gallery path serves gallery.html
- [x] Command: `python manage.py serve --reload`
- [x] Photo serving from /photos/* → prod/pics/*
- [ ] Debug photo display issues (images not loading)
- [ ] Live browser refresh on changes

##### Implementation Status
- ✅ TDD tests for dev server (14 tests passing)
- ✅ Custom HTTP handler with routing
- ✅ File watcher with watchdog library
- ✅ Fixed build command template path (src/template/)
- ✅ Fixed PhotoMetadataService URL generation
- 🚧 Photo serving implementation needs debugging
- ⏳ Browser auto-refresh (WebSocket/SSE) - low priority

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

#### Build Command Implementation Approach

**TDD Strategy**: Strict separation of concerns
- **Command module**: Terminal I/O only (status messages, error reporting)
- **Service modules**: All actual work (directory creation, file generation, etc.)

**Implementation Steps**:

1. **Build command basics** (test/command/test_build.py) ✅
   - Command exists and is callable
   - Outputs status messages with keywords: build, site, generating

2. **Site generator service** (test/services/test_site_generator.py) ✅
   - Creates directory structure: prod/site/, prod/site/css/, prod/site/js/
   - Reports what directories were created/already exist

3. **Photo metadata service** (test/services/test_photo_metadata.py) [x]
   - Scans prod/pics/ for processed photos
   - Extracts metadata from chronological filenames
   - Generates JSON structure for frontend

4. **Template rendering service** (test/services/test_template_renderer.py)
   - Renders Jinja2 templates with photo data [x]
   - Generates HTML files to output directory [x]
   - Separate template tests for HTML content validation

5. **Static asset service** (test/services/test_static_assets.py) [x]
   - Copies CSS/JS files to output
   - Generates photos.json API endpoint

**Key Principles**:
- Command module ONLY handles terminal I/O
- Each service has single responsibility
- TDD: Write failing test → implement → refactor
- No CLI options until MVP complete

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

### Dynamic Loading & Performance

**Deliverable**: Progressive loading optimization for large photo collections

#### Acceptance Criteria

- [ ] **Infinite Scroll Loading**: Split photo rendering between initial batch (server-side) and progressive loading (JS)
- [ ] **Lazy Loading**: Progressive image loading optimization
- [ ] **Performance Monitoring**: Real-world performance metrics collection
- [ ] **BunnyCDN Analytics Integration**: Parse CDN access logs for photo popularity tracking
- [ ] **Popularity-Based Ordering**: Sort photos by download frequency from CDN logs

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

