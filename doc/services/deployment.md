# Deployment Service

The deployment service provides intelligent, metadata-driven deployment capabilities for Galleria photo galleries. It implements atomic operations, hash-based change detection, and comprehensive error handling for reliable production deployments.

## Overview

The deployment service orchestrates the complete deployment process from local galleries to S3-compatible storage, ensuring consistency and enabling selective updates based on file changes.

**Key Features:**
- **Atomic deployments** by uploading metadata last
- **Incremental updates** by comparing `deployment_file_hash` values
- **Dry-run capability** for testing deployment plans
- **State verification** to ensure remote consistency
- **Photo lifecycle management** including deletion of orphaned files

## Core Functions

### `deploy_gallery_metadata()`

The main deployment orchestration function that coordinates the entire process.

```python
def deploy_gallery_metadata(
    client,
    bucket: str,
    local_metadata: GalleryMetadata,
    prod_dir: Path,
    dry_run: bool = False
) -> Dict[str, Any]
```

**Purpose:** Deploy complete gallery with metadata-last upload ordering for atomic consistency.

**Process:**
1. Downloads remote metadata for comparison
2. Generates deployment plan based on hash differences
3. Uploads changed photos using EXIF modification streaming
4. Uploads metadata last to ensure atomic consistency

**Returns:**
```python
{
    'success': bool,
    'dry_run': bool,
    'photos_uploaded': int,
    'metadata_uploaded': bool,
    'plan': Dict,  # if dry_run=True
    'message': str,
    'error': str   # if failed
}
```

**Example Usage:**
```python
from src.services.deployment import deploy_gallery_metadata
from src.models.photo import GalleryMetadata

# Load local metadata
metadata = GalleryMetadata.from_dict(json_data)

# Deploy to production
result = deploy_gallery_metadata(
    client=s3_client,
    bucket="my-gallery-bucket",
    local_metadata=metadata,
    prod_dir=Path("prod/pics"),
    dry_run=False
)

if result['success']:
    print(f"Deployed {result['photos_uploaded']} photos")
else:
    print(f"Deployment failed: {result['error']}")
```

### `generate_deployment_plan()`

Compares local and remote metadata to determine what needs to be uploaded or deleted.

```python
def generate_deployment_plan(
    local_metadata: GalleryMetadata, 
    remote_metadata: Optional[GalleryMetadata]
) -> Dict[str, List]
```

**Purpose:** Generate deployment plan by comparing `deployment_file_hash` values between local and remote metadata.

**Logic:**
- **Upload**: Photos with different hashes or new photos
- **Delete**: Remote photos not present locally
- **Unchanged**: Photos with matching hashes

**Returns:**
```python
{
    'upload': List[PhotoMetadata],    # Photos to upload
    'delete': List[str],              # Photo IDs to delete
    'unchanged': List[PhotoMetadata]  # Photos that are unchanged
}
```

**Example Usage:**
```python
plan = generate_deployment_plan(local_metadata, remote_metadata)

print(f"Will upload {len(plan['upload'])} photos")
print(f"Will delete {len(plan['delete'])} photos")
print(f"Unchanged: {len(plan['unchanged'])} photos")
```

### `download_remote_metadata()`

Downloads and parses metadata from remote storage.

```python
def download_remote_metadata(client, bucket: str, key: str) -> Optional[GalleryMetadata]
```

**Purpose:** Download and parse remote `gallery-metadata.json` from S3 bucket.

**Error Handling:**
- Returns `None` if file doesn't exist (`NoSuchKey`)
- Returns `None` if JSON is invalid or corrupted
- Raises other S3 client errors

**Example Usage:**
```python
remote_metadata = download_remote_metadata(
    client=s3_client,
    bucket="my-gallery-bucket", 
    key="gallery-metadata.json"
)

if remote_metadata:
    print(f"Found {len(remote_metadata.photos)} remote photos")
else:
    print("No remote metadata found")
```

### `verify_s3_state()`

Validates that remote S3 state matches expected metadata.

```python
def verify_s3_state(client, bucket: str, metadata: GalleryMetadata) -> Dict[str, Any]
```

**Purpose:** Verify remote state consistency by comparing actual S3 files against metadata expectations.

**Returns:**
```python
{
    'consistent': bool,
    'missing_files': List[str],  # Expected files not in S3
    'orphaned_files': List[str]  # S3 files not in metadata
}
```

**Example Usage:**
```python
verification = verify_s3_state(s3_client, "my-bucket", metadata)

if not verification['consistent']:
    print(f"Missing files: {verification['missing_files']}")
    print(f"Orphaned files: {verification['orphaned_files']}")
```

### `deploy_directory_to_s3()`

Legacy directory-based deployment for backward compatibility.

```python
def deploy_directory_to_s3(
    client,
    source_dir: Path,
    bucket: str,
    prefix: str = "",
    dry_run: bool = False,
    progress_callback: Optional[Callable[[str, int, int], None]] = None
) -> Dict[str, Any]
```

**Purpose:** Deploy entire directory to S3 without metadata optimization. Used as fallback when `gallery-metadata.json` doesn't exist.

**Returns:**
```python
{
    'success': bool,
    'total_files': int,
    'uploaded_files': int,
    'skipped_files': int,
    'failed_files': int,
    'total_size': int,
    'errors': List[str],
    'error': str  # if validation failed
}
```

## Integration with Deploy Command

The deployment service is primarily used by the enhanced deploy command:

```python
# In src/command/deploy.py
from src.services.deployment import deploy_gallery_metadata

# Automatic mode detection
metadata_file = photos_dir / "gallery-metadata.json"
if metadata_file.exists():
    # Use metadata-driven deployment
    local_metadata = load_local_gallery_metadata(photos_dir)
    result = deploy_gallery_metadata(
        client=client,
        bucket=bucket,
        local_metadata=local_metadata,
        prod_dir=photos_dir,
        dry_run=dry_run
    )
else:
    # Fallback to directory deployment
    result = deploy_directory_to_s3(...)
```

## Deployment Hash System

The service relies on the dual-hash metadata system for change detection:

- **`file_hash`**: SHA256 of original source file
- **`deployment_file_hash`**: SHA256 of file after EXIF modifications

**Why deployment hashes matter:**
- Detects changes to processing settings (`TIMESTAMP_OFFSET_HOURS`, `TARGET_TIMEZONE_OFFSET_HOURS`)
- Accounts for EXIF modification transformations
- Enables byte-level change detection for selective uploads

## Atomic Operations

The service ensures atomic deployments through metadata-last upload ordering:

1. **Upload photos first**: All photo variants (full, web, thumb)
2. **Upload metadata last**: `gallery-metadata.json` reflects actual remote state
3. **Consistency guarantee**: Metadata always matches deployed photos

**Benefits:**
- Partial failures don't corrupt remote state
- Deployments can be safely retried
- Remote metadata always reflects actual files
- Enables reliable incremental deployments

## Error Handling

The service provides comprehensive error handling:

**Network Errors:**
```python
try:
    result = deploy_gallery_metadata(...)
    if not result['success']:
        handle_deployment_error(result['error'])
except ClientError as e:
    handle_s3_error(e)
```

**Validation Errors:**
- Missing source directories
- Invalid metadata JSON
- S3 configuration issues
- Permission errors

**Recovery Patterns:**
- Retry failed deployments (metadata consistency preserved)
- Verify state before retry attempts
- Log detailed error information for debugging

## Performance Characteristics

**Metadata-Driven Benefits:**
- **Selective uploads**: Only changed files are uploaded
- **Bandwidth optimization**: Skips unchanged photos
- **Resume capability**: Partial failures are recoverable
- **Parallel uploads**: Photos can be uploaded concurrently

**Scaling Considerations:**
- Memory usage scales with metadata size (not photo count)
- Network usage scales with changed files only
- S3 API calls scale with total file count (for state verification)

## Testing

The service includes comprehensive test coverage:

```bash
# Run deployment service tests
uv run pytest test/services/test_deployment.py -v

# Run integration tests
uv run pytest test/command/test_deploy_integration.py -v
```

**Test Coverage:**
- 21 unit tests covering all deployment scenarios
- Integration tests with end-to-end workflows
- Error condition testing
- Dry-run mode validation
- State verification testing

## See Also

- **[Deploy Command](../command/deploy.md)**: CLI interface using this service
- **[Metadata Consistency](../architecture/metadata-consistency.md)**: Dual-hash system architecture
- **[S3 Storage Service](s3_storage.md)**: Low-level S3 operations and EXIF modification
- **[Settings System](../settings.md)**: Configuration for S3 credentials and deployment settings