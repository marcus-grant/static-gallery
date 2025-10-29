# S3 Storage Service

The S3 storage service provides comprehensive S3-compatible cloud storage operations for Galleria, including file uploads, EXIF modification, and deployment capabilities. It supports any S3-compatible service (AWS S3, Hetzner Object Storage, DigitalOcean Spaces, etc.).

## Overview

The S3 storage service handles all cloud storage interactions for Galleria deployments. It provides low-level upload operations, in-memory EXIF modification, and batch deployment capabilities with comprehensive progress tracking and error handling.

**Key Features:**
- **Multi-provider support**: Works with any S3-compatible service
- **In-memory EXIF modification**: Modifies photo metadata without temporary files
- **Streaming uploads**: Memory-efficient uploads with progress tracking
- **Duplicate detection**: Optimizes deployments by skipping existing files
- **Batch operations**: Efficiently handles large file collections

## Core Functions

### S3 Client Management

#### `get_s3_client()`

Creates configured S3 client for any S3-compatible service.

```python
def get_s3_client(endpoint: str, access_key: str, secret_key: str, region: str)
```

**Purpose:** Initialize boto3 S3 client with custom endpoint support for non-AWS services.

**Example Usage:**
```python
from src.services.s3_storage import get_s3_client

# AWS S3
client = get_s3_client(
    endpoint="https://s3.amazonaws.com",
    access_key="AKIA...",
    secret_key="secret...",
    region="us-east-1"
)

# Hetzner Object Storage  
client = get_s3_client(
    endpoint="https://fsn1.your-objectstorage.com",
    access_key="access_key",
    secret_key="secret_key", 
    region="us-east-1"
)
```

### File Operations

#### `upload_file_to_s3()`

Uploads single file with duplicate detection and progress tracking.

```python
def upload_file_to_s3(
    client, 
    local_path: Path, 
    bucket: str, 
    key: str, 
    progress_callback: Optional[Callable[[int], None]] = None
) -> Dict[str, Any]
```

**Purpose:** Upload single file to S3 with checksum calculation and duplicate detection.

**Returns:**
```python
{
    'success': bool,
    'skipped': bool,        # If file already exists
    'file_size': int,
    'checksum': str,        # SHA256 hash
    'upload_time': float,   # Seconds
    'error': str           # If failed
}
```

**Example Usage:**
```python
def progress_callback(bytes_transferred):
    print(f"Uploaded {bytes_transferred} bytes")

result = upload_file_to_s3(
    client=s3_client,
    local_path=Path("photo.jpg"),
    bucket="my-gallery",
    key="photos/photo.jpg",
    progress_callback=progress_callback
)

if result['success']:
    if result['skipped']:
        print("File already exists, skipped")
    else:
        print(f"Uploaded {result['file_size']} bytes")
```

#### `upload_directory_to_s3()`

Recursively uploads entire directories with batch progress tracking.

```python
def upload_directory_to_s3(
    client,
    local_dir: Path,
    bucket: str,
    prefix: str = '',
    dry_run: bool = False,
    progress_callback: Optional[Callable[[str, int, int], None]] = None
) -> Dict[str, Any]
```

**Purpose:** Upload complete directory structures to S3 while preserving folder hierarchy.

**Returns:**
```python
{
    'success': bool,
    'total_files': int,
    'uploaded_files': int,
    'skipped_files': int,
    'failed_files': int,
    'total_size': int,
    'upload_time': float,
    'errors': List[str]
}
```

**Example Usage:**
```python
def progress_callback(filename, current, total):
    print(f"[{current}/{total}] Uploading {filename}")

result = upload_directory_to_s3(
    client=s3_client,
    local_dir=Path("prod/pics"),
    bucket="my-gallery",
    prefix="photos",
    dry_run=False,
    progress_callback=progress_callback
)

print(f"Uploaded {result['uploaded_files']}/{result['total_files']} files")
print(f"Total size: {result['total_size']} bytes")
```

### EXIF Modification

#### `modify_exif_in_memory()`

Modifies JPEG EXIF metadata in memory without creating temporary files.

```python
def modify_exif_in_memory(
    image_bytes: bytes, 
    corrected_timestamp: datetime, 
    target_timezone_offset_hours: int
) -> bytes
```

**Purpose:** Modify EXIF metadata for timestamp correction and timezone setting without disk I/O.

**EXIF Modifications:**
- **`DateTimeOriginal`**: Updated with corrected timestamp
- **`OffsetTimeOriginal`**: Set to timezone offset in `±HH:MM` format
- **Special handling**: `target_timezone_offset_hours=13` preserves original timezone

**Example Usage:**
```python
from datetime import datetime
from src.services.s3_storage import modify_exif_in_memory

# Read image file
with open("photo.jpg", "rb") as f:
    image_bytes = f.read()

# Correct timestamp (camera was 2 hours fast)
corrected_time = datetime(2024, 6, 15, 10, 30, 45)

# Apply Eastern timezone (-5 hours)
modified_bytes = modify_exif_in_memory(
    image_bytes=image_bytes,
    corrected_timestamp=corrected_time,
    target_timezone_offset_hours=-5
)

# Upload modified image directly
upload_file_to_s3(client, modified_bytes, bucket, key)
```

### Utility Functions

#### `file_exists_in_s3()`

Checks if file already exists in S3 bucket.

```python
def file_exists_in_s3(client, bucket: str, key: str) -> bool
```

**Purpose:** Optimize uploads by detecting existing files to avoid duplicate transfers.

#### `calculate_file_checksum()`

Computes SHA256 checksum for file integrity verification.

```python
def calculate_file_checksum(file_path: Path) -> str
```

**Purpose:** Generate file checksums for integrity verification and change detection.

#### `list_bucket_files()`

Lists all files in S3 bucket with optional prefix filtering.

```python
def list_bucket_files(client, bucket: str, prefix: str = '') -> list
```

**Purpose:** Bucket management and state verification for deployment consistency.

## CORS Management

The S3 storage service provides comprehensive CORS (Cross-Origin Resource Sharing) management for bucket configuration.

### CORS Functions

#### `get_bucket_cors()`

Retrieves current CORS configuration from an S3 bucket.

```python
def get_bucket_cors(client, bucket: str) -> Dict[str, Any]
```

**Returns:**
- `success`: Boolean indicating operation success
- `cors_rules`: List of current CORS rules (empty if none configured)
- `error`: Error message if operation failed

#### `configure_bucket_cors()`

Sets CORS rules for an S3 bucket.

```python
def configure_bucket_cors(client, bucket: str, cors_rules: list) -> Dict[str, Any]
```

**Purpose:** Apply CORS configuration to enable web access for gallery photos.

#### `get_default_gallery_cors_rules()`

Returns optimal CORS rules for gallery web access.

```python
def get_default_gallery_cors_rules() -> list
```

**Default Rules:**
- **AllowedMethods**: `["GET", "HEAD"]` (read-only access)
- **AllowedOrigins**: `["*"]` (all domains for CDN compatibility)
- **AllowedHeaders**: `["*"]` (flexible header support)
- **ExposeHeaders**: `["ETag"]` (cache optimization)
- **MaxAgeSeconds**: `3600` (1-hour preflight cache)

#### `cors_rules_match()`

Compares current CORS rules with expected rules.

```python
def cors_rules_match(current_rules: list, expected_rules: list) -> bool
```

**Purpose:** Determine if CORS configuration needs updating.

#### `examine_bucket_cors()`

Comprehensive CORS examination with comparison and recommendations.

```python
def examine_bucket_cors(client, bucket: str) -> Dict[str, Any]
```

**Returns:**
- `success`: Boolean indicating examination success
- `configured`: Boolean indicating if any CORS rules exist
- `current_rules`: List of current CORS rules
- `expected_rules`: List of recommended CORS rules
- `needs_update`: Boolean indicating if rules need updating

### CORS Usage Examples

```python
from src.services.s3_storage import (
    examine_bucket_cors, 
    configure_bucket_cors, 
    get_default_gallery_cors_rules
)

# Examine current CORS configuration
cors_status = examine_bucket_cors(client, "gallery-bucket")

if cors_status['needs_update']:
    # Apply recommended CORS rules
    rules = get_default_gallery_cors_rules()
    result = configure_bucket_cors(client, "gallery-bucket", rules)
    
    if result['success']:
        print("CORS configured successfully")
    else:
        print(f"CORS configuration failed: {result['error']}")
```

### Deploy Command Integration

The CORS functions are automatically used by the deploy command:

```python
# Automatic CORS validation in deploy command
cors_examination = examine_bucket_cors(client, bucket)

if not cors_examination['configured'] or cors_examination['needs_update']:
    if setup_cors_flag:
        # Configure CORS automatically
        configure_bucket_cors(client, bucket, get_default_gallery_cors_rules())
    else:
        # Abort deployment with guidance
        print("Use --setup-cors to configure CORS for web access")
        sys.exit(1)
```

## Integration with Deployment System

The S3 storage service is the foundation for Galleria's deployment capabilities:

### Metadata-Driven Deployments

```python
# In deployment.py
from src.services.s3_storage import modify_exif_in_memory, upload_file_to_s3

# Upload photo with EXIF correction
with open(photo_path, 'rb') as f:
    image_bytes = f.read()

# Apply timestamp and timezone corrections
modified_bytes = modify_exif_in_memory(
    image_bytes, 
    corrected_timestamp, 
    target_timezone_offset
)

# Stream upload without temporary files
result = upload_file_to_s3(
    client, modified_bytes, bucket, s3_key
)
```

### Directory Deployments

```python
# Deploy complete photo directory
result = upload_directory_to_s3(
    client=s3_client,
    local_dir=Path("prod/pics"),
    bucket="gallery-bucket",
    prefix="photos",
    dry_run=False
)
```

### Progress Tracking

```python
def deployment_progress(filename, current, total):
    percentage = (current / total) * 100
    print(f"[{percentage:.1f}%] {filename}")

upload_directory_to_s3(
    # ... other params
    progress_callback=deployment_progress
)
```

## EXIF Modification Details

### Dual Timezone System

The EXIF modification supports Galleria's dual timezone correction system:

1. **Timestamp Correction**: `corrected_timestamp` parameter
   - Fixes systematic camera time errors
   - Applied to `DateTimeOriginal` EXIF field

2. **Timezone Context**: `target_timezone_offset_hours` parameter
   - Sets actual timezone information
   - Written to `OffsetTimeOriginal` field
   - Format: `±HH:MM` (e.g., `-05:00`, `+02:00`)

### Special Timezone Handling

```python
# Preserve original timezone (no modification)
modify_exif_in_memory(image_bytes, timestamp, 13)

# Apply Eastern timezone (-5 hours)
modify_exif_in_memory(image_bytes, timestamp, -5)

# Apply Central European timezone (+1 hour)
modify_exif_in_memory(image_bytes, timestamp, 1)
```

### EXIF 2.31 Compliance

The modification follows EXIF 2.31 standard:
- **Timezone format**: ISO 8601 style (`±HH:MM`)
- **Field usage**: `OffsetTimeOriginal` for timezone context
- **Timestamp format**: Standard EXIF datetime format
- **Error handling**: Creates empty EXIF structure if none exists

## Performance Characteristics

### Memory Efficiency

- **Streaming operations**: Files processed in 4KB chunks
- **No temporary files**: EXIF modification happens in memory
- **Progress tracking**: Real-time feedback without memory overhead

### Network Optimization

- **Duplicate detection**: Avoids re-uploading existing files
- **Batch operations**: Efficient handling of large file sets
- **Error resilience**: Continues uploads despite individual failures

### Scaling Considerations

- **Memory usage**: Scales with largest individual file size, not collection size
- **Network usage**: Scales with changed files only (when using duplicate detection)
- **API calls**: Minimal S3 API usage through efficient batching

## Error Handling

The service provides comprehensive error handling:

### File-Level Errors
```python
result = upload_file_to_s3(...)
if not result['success']:
    print(f"Upload failed: {result['error']}")
    # Handle individual file failure
```

### Directory-Level Errors
```python
result = upload_directory_to_s3(...)
if result['failed_files'] > 0:
    print(f"Failed files: {result['errors']}")
    # Handle batch operation failures
```

### Network Errors
- Connection timeouts
- Authentication failures
- Permission errors
- Storage quota issues

## Configuration

The service requires S3 credentials and endpoint configuration:

```python
# From settings
S3_PUBLIC_ENDPOINT = "https://your-s3-endpoint.com"
S3_PUBLIC_ACCESS_KEY = "your-access-key"
S3_PUBLIC_SECRET_KEY = "your-secret-key"
S3_PUBLIC_BUCKET = "your-bucket-name"
S3_PUBLIC_REGION = "your-region"
```

## Testing

The service includes comprehensive test coverage:

```bash
# Run S3 storage tests
uv run pytest test/services/test_s3_storage.py -v

# Run EXIF modification tests
uv run pytest test/services/test_s3_storage.py::TestExifModification -v

# Run CORS configuration tests
uv run pytest test/services/test_s3_storage.py::TestCORSConfiguration -v
```

**Test Coverage:**
- EXIF modification with various timezone scenarios
- Upload operations with progress tracking
- Error handling and edge cases
- Duplicate detection logic
- Directory upload operations
- CORS configuration and validation
- CORS rules comparison and matching
- Bucket CORS examination and reporting

## See Also

- **[Deployment Service](deployment.md)**: High-level deployment orchestration using this service
- **[EXIF Modification Service](exif_modification.md)**: Detailed EXIF modification documentation
- **[Settings System](../settings.md)**: S3 configuration and credentials
- **[Deploy Command](../command/deploy.md)**: CLI interface for deployment operations