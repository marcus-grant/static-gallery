# File Processing Service

The file processing service is the central orchestrator for photo collection processing in Galleria. It handles the complete pipeline from raw photos to web-ready galleries with metadata, thumbnails, and chronological organization.

## Overview

The file processing service transforms photo collections into structured galleries with comprehensive metadata tracking. It implements efficient incremental processing, dual-hash integrity verification, and timezone-aware metadata generation.

**Key Responsibilities:**
- **Photo Collection Processing**: Organizes photos chronologically with generated filenames
- **File Organization**: Creates symlinks for storage efficiency (no file duplication)
- **Thumbnail Generation**: Creates WebP thumbnails optimized for web display
- **Metadata Management**: Generates comprehensive gallery metadata with dual-hash tracking
- **Dual Collection Support**: Handles both single and dual collection workflows

## Core Functions

### Collection Processing

#### `process_dual_photo_collection()`

Main entry point for processing photo collections with full and web-optimized versions.

```python
def process_dual_photo_collection(
    full_source_dir: Path, 
    web_source_dir: Path, 
    output_dir: Path, 
    collection_name: str
) -> dict
```

**Purpose:** Process dual collections (full resolution + web-optimized) with validation and incremental processing.

**Process:**
1. Validates matching between full and web collections
2. Extracts EXIF metadata and generates chronological filenames
3. Creates symlinks with organized structure
4. Generates WebP thumbnails
5. Calculates dual-hash metadata (original + deployment)
6. Saves comprehensive gallery metadata JSON

**Returns:**
```python
{
    'success': bool,
    'photos_processed': int,
    'thumbnails_created': int,
    'symlinks_created': int,
    'errors': List[str],
    'photos': List[ProcessedPhoto]
}
```

**Example Usage:**
```python
from src.services.file_processing import process_dual_photo_collection

result = process_dual_photo_collection(
    full_source_dir=Path("photos/full"),
    web_source_dir=Path("photos/web"),
    output_dir=Path("prod/pics"),
    collection_name="wedding-2024"
)

if result['success']:
    print(f"Processed {result['photos_processed']} photos")
    print(f"Created {result['thumbnails_created']} thumbnails")
else:
    print(f"Errors: {result['errors']}")
```

#### `process_photo_collection()`

Processes single photo collection.

```python
def process_photo_collection(
    source_dir: Path, 
    output_dir: Path, 
    collection_name: str
) -> dict
```

**Purpose:** Process single collection of photos for simpler workflows.

### File Operations

#### `link_photo_with_filename()`

Creates organized symlinks with chronological filenames.

```python
def link_photo_with_filename(photo: ProcessedPhoto, output_dir: Path) -> Path
```

**Purpose:** Create symlinks in organized directory structure without duplicating files.

**Directory Structure:**
```
output_dir/
├── full/           # Full resolution symlinks
├── web/            # Web-optimized symlinks
├── thumb/          # WebP thumbnails
└── gallery-metadata.json
```

**Filename Format:** `collection-YYYYMMDDTHHMMSS-camera-counter.jpg`
- Example: `wedding-20240615T143045-r5a-0.jpg`

#### `create_thumbnail()`

Generates optimized WebP thumbnails for web display.

```python
def create_thumbnail(source_path: Path, thumb_path: Path) -> bool
```

**Purpose:** Create web-optimized thumbnails with consistent quality and format.

**Specifications:**
- **Format**: WebP for optimal compression
- **Max dimension**: 400px (maintains aspect ratio)
- **Quality**: 85% for balance of size vs quality
- **Resampling**: LANCZOS for high-quality scaling

### Metadata Generation

#### `generate_gallery_metadata()`

Creates comprehensive gallery metadata with dual-hash tracking.

```python
def generate_gallery_metadata(photos: List[ProcessedPhoto], collection_name: str) -> GalleryMetadata
```

**Purpose:** Generate complete metadata structure for deployment and gallery rendering.

**Metadata Includes:**
- Original and corrected timestamps
- Camera information (make, model)
- File paths for all variants (full, web, thumb)
- Dual-hash system (original + deployment hashes)
- Timezone and processing settings

**Example Output:**
```json
{
  "schema_version": "1.0",
  "generated_at": "2024-10-28T10:00:00Z",
  "collection": "wedding-2024",
  "settings": {
    "timestamp_offset_hours": -4
  },
  "photos": [
    {
      "id": "wedding-20240615T143045-r5a-0",
      "original_path": "/src/photos/IMG_1234.jpg",
      "file_hash": "abc123...",
      "deployment_file_hash": "def456...",
      "exif": {
        "original_timestamp": "2024-06-15T18:30:45",
        "corrected_timestamp": "2024-06-15T14:30:45",
        "timezone_original": "+00:00",
        "camera": {"make": "Canon", "model": "EOS R5"}
      },
      "files": {
        "full": "photos/full/wedding-20240615T143045-r5a-0.jpg",
        "web": "photos/web/wedding-20240615T143045-r5a-0.jpg",
        "thumb": "photos/thumb/wedding-20240615T143045-r5a-0.webp"
      }
    }
  ]
}
```

## Dual-Hash Metadata System

The service implements a sophisticated dual-hash system for comprehensive file tracking:

### Original File Hash
```python
photo.file_hash = calculate_file_checksum(full_path)
```

**Purpose:** Track integrity of original source files
- SHA256 hash of unmodified source file
- Detects changes to source photos
- Enables source file verification

### Deployment File Hash
```python
# Simulate EXIF modification for deployment hash
with open(full_path, 'rb') as f:
    image_bytes = f.read()

modified_bytes = modify_exif_in_memory(
    image_bytes, 
    corrected_timestamp, 
    target_timezone_offset_hours
)

deployment_hash = hashlib.sha256(modified_bytes).hexdigest()
```

**Purpose:** Track files after EXIF timezone modifications
- Hash of file with applied timezone corrections
- Enables deployment change detection
- Accounts for processing setting changes

### Benefits of Dual-Hash System

1. **Integrity Verification**: Ensure source files haven't changed
2. **Deployment Optimization**: Only upload files with changed deployment hashes
3. **Settings Sensitivity**: Detect when timezone settings change require redeployment
4. **Error Detection**: Identify corruption in either source or processed files

## Incremental Processing

The service implements intelligent incremental processing to optimize performance:

### `is_processing_needed()`

```python
def is_processing_needed(
    full_path: Path, 
    web_path: Path, 
    output_dir: Path, 
    generated_filename: str
) -> bool
```

**Logic:**
1. Check if output files exist (symlinks and thumbnail)
2. Compare modification times (outputs newer than sources)
3. Skip processing if outputs are up-to-date

**Benefits:**
- **Performance**: Skip unchanged photos
- **Efficiency**: Only process new or modified files
- **Resumability**: Safely restart interrupted processing

## Integration with Pipeline

### Input Dependencies

The service integrates with multiple Galleria components:

```python
# EXIF extraction
from src.services.exif import get_datetime_taken, get_camera_info, extract_exif_data

# Filename generation
from src.services.filename_service import generate_photo_filename

# File validation
from src.services.photo_validation import validate_matching_collections

# Storage operations
from src.services.s3_storage import calculate_file_checksum, modify_exif_in_memory
```

### Settings Integration

Uses global settings for timezone handling:

```python
import settings

# Apply timestamp corrections
corrected_timestamp = original_timestamp + timedelta(hours=settings.TIMESTAMP_OFFSET_HOURS)

# Calculate deployment hash with timezone
deployment_hash = calculate_deployment_hash(
    image_bytes, 
    corrected_timestamp, 
    settings.TARGET_TIMEZONE_OFFSET_HOURS
)
```

### Output Structure

Creates organized directory structure:

```
prod/pics/
├── full/
│   ├── wedding-20240615T143045-r5a-0.jpg -> ../../source/IMG_1234.jpg
│   └── wedding-20240615T143212-r5a-1.jpg -> ../../source/IMG_1235.jpg
├── web/
│   ├── wedding-20240615T143045-r5a-0.jpg -> ../../source-web/IMG_1234.jpg
│   └── wedding-20240615T143212-r5a-1.jpg -> ../../source-web/IMG_1235.jpg
├── thumb/
│   ├── wedding-20240615T143045-r5a-0.webp
│   └── wedding-20240615T143212-r5a-1.webp
└── gallery-metadata.json
```

## Error Handling

The service provides comprehensive error handling and reporting:

### Processing Errors
```python
result = process_dual_photo_collection(...)
if not result['success']:
    for error in result['errors']:
        print(f"Processing error: {error}")
```

### Common Error Scenarios
- **Missing EXIF data**: Photos without timestamps
- **Mismatched collections**: Full/web photos don't correspond
- **Permission errors**: Can't create symlinks or thumbnails
- **Corrupted files**: Invalid image formats or damaged files
- **File system errors**: Disk space, path issues

### Error Recovery
- **Partial processing**: Continues with other photos if individual files fail
- **Error collection**: Aggregates all errors for comprehensive reporting
- **State preservation**: Doesn't corrupt existing outputs on failures

## Performance Characteristics

### Memory Efficiency
- **Streaming operations**: Processes photos individually
- **No file duplication**: Uses symlinks instead of copying
- **Incremental processing**: Skips unchanged files

### Storage Optimization
- **Symlink structure**: Minimal disk usage increase
- **WebP thumbnails**: Optimal compression for web display
- **Organized layout**: Efficient file system structure

### Processing Speed
- **Parallel potential**: Photos can be processed independently
- **Incremental updates**: Only processes changed files
- **Optimized thumbnails**: Efficient image scaling algorithms

## Usage Examples

### Basic Collection Processing
```python
from pathlib import Path
from src.services.file_processing import process_dual_photo_collection

# Process wedding photos
result = process_dual_photo_collection(
    full_source_dir=Path("source/full"),
    web_source_dir=Path("source/web"),
    output_dir=Path("prod/pics"),
    collection_name="wedding-ceremony"
)

print(f"Success: {result['success']}")
print(f"Photos processed: {result['photos_processed']}")
```

### Incremental Processing
```python
# Second run only processes new/changed photos
result = process_dual_photo_collection(
    # Same parameters - only new photos will be processed
)
```

### Error Handling
```python
result = process_dual_photo_collection(...)

if result['errors']:
    print("Encountered errors:")
    for error in result['errors']:
        print(f"  - {error}")
    
    print(f"Still processed {result['photos_processed']} photos successfully")
```

## See Also

- **[EXIF Service](exif_modification.md)**: EXIF data extraction and modification
- **[S3 Storage Service](s3_storage.md)**: File checksum calculation and EXIF modification
- **[Deployment Service](deployment.md)**: Uses metadata generated by this service
- **[Settings System](../settings.md)**: Timezone and processing configuration
- **[Process Photos Command](../command/process-photos.md)**: CLI interface for this service