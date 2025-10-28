# Deploy Command

The `deploy` command uploads your complete gallery (photos + static site) to production hosting with intelligent metadata-driven deployment.

## Overview

The deploy command automatically detects whether you have gallery metadata and chooses the optimal deployment strategy:

- **Metadata-driven deployment**: When `gallery-metadata.json` exists, uses hash-based comparison for selective uploads
- **Directory-based deployment**: Fallback mode for legacy workflows without metadata

## Usage

```bash
python manage.py deploy [OPTIONS]
```

## Command Options

### Basic Options
- `--source, -s PATH`: Override OUTPUT_DIR for source directory
- `--dry-run`: Show deployment plan without executing
- `--photos-only`: Upload only photos/metadata (skip static site)
- `--site-only`: Upload only static site files (skip photos)

### Advanced Options
- `--force`: Upload all photos ignoring hash comparison *(coming soon)*
- `--progress`: Show detailed progress during upload *(coming soon)*
- `--invalidate-cdn`: Trigger CDN cache purge *(coming soon)*

## Deployment Modes

### Metadata-Driven Deployment (Recommended)

When `prod/pics/gallery-metadata.json` exists, the deploy command uses the Phase 4 deployment orchestration system:

```bash
# Standard metadata-driven deployment
python manage.py deploy

# Show deployment plan without uploading
python manage.py deploy --dry-run

# Deploy only photos with metadata comparison
python manage.py deploy --photos-only
```

**Features:**
- Hash-based change detection using `deployment_file_hash`
- Atomic operations with metadata-last upload ordering
- EXIF modification streaming (no local temporary files)
- Selective uploads (only changed photos)
- Deployment plan visualization

### Directory-Based Deployment (Legacy)

When no metadata exists, falls back to directory-based uploads:

```bash
# Upload entire directories
python manage.py deploy --site-only
```

**Features:**
- Uploads all files in directories
- Compatible with existing workflows
- No hash-based optimization

## Examples

### Complete Gallery Deployment

```bash
# Process photos and deploy everything
python manage.py process-photos
python manage.py build
python manage.py deploy
```

### Dry Run Before Deployment

```bash
# See what would be deployed
python manage.py deploy --dry-run

# Example output:
# [DRY RUN] Using metadata-driven deployment...
# Bucket: my-gallery-bucket
#
# Deployment Plan:
#   Photos to upload: 3
#   Photos to delete: 0
#   Photos unchanged: 15
#
# Dry run completed - no files were uploaded
```

### Photos-Only Deployment

```bash
# Deploy only photos, skip static site
python manage.py deploy --photos-only
```

### Development Workflow

```bash
# Build and deploy static site changes
python manage.py build
python manage.py deploy --site-only
```

## Configuration Requirements

The deploy command requires S3-compatible storage configuration:

```python
# settings.local.py or environment variables
S3_PUBLIC_ENDPOINT = "https://your-s3-endpoint.com"
S3_PUBLIC_ACCESS_KEY = "your-access-key"
S3_PUBLIC_SECRET_KEY = "your-secret-key"
S3_PUBLIC_BUCKET = "your-bucket-name"
S3_PUBLIC_REGION = "your-region"
```

## Deployment Process

### Metadata-Driven Process

1. **Load local metadata** from `prod/pics/gallery-metadata.json`
2. **Download remote metadata** from S3 bucket
3. **Generate deployment plan** by comparing `deployment_file_hash` values
4. **Upload photos** (changed files only)
5. **Upload static site** (if not photos-only)
6. **Upload metadata last** (atomic consistency)

### Directory-Based Process

1. **Upload photos directory** to `photos/` prefix (if not site-only)
2. **Upload static site directory** to bucket root (if not photos-only)

## Error Handling

The deploy command provides comprehensive error handling:

```bash
# S3 configuration errors
Error: Missing S3 configuration
Please configure S3 settings in settings.local.py or environment variables:
  - GALLERIA_S3_PUBLIC_ENDPOINT
  - GALLERIA_S3_PUBLIC_ACCESS_KEY
  # ... etc

# Metadata errors
Error loading gallery metadata: Gallery metadata not found: /path/to/gallery-metadata.json

# Deployment failures
Photo deployment failed: Connection timeout
Static site deployment failed: Permission denied
```

## Integration with Processing Pipeline

The deploy command integrates seamlessly with the photo processing pipeline:

1. **`process-photos`**: Generates `gallery-metadata.json` with deployment hashes
2. **`build`**: Creates static site in `OUTPUT_DIR`
3. **`deploy`**: Uploads using metadata comparison or directory fallback

## Performance Characteristics

### Metadata-Driven Advantages

- **Selective uploads**: Only changed photos are uploaded
- **Hash verification**: Detects changes at byte level
- **Atomic consistency**: Metadata always reflects actual remote state
- **Bandwidth optimization**: Skips unchanged files
- **Resume capability**: Partial failures don't corrupt state

### Deployment Hash System

Photos are compared using `deployment_file_hash` which reflects:
- Original photo content
- EXIF timestamp corrections
- Timezone settings
- EXIF modification transformations

This ensures deployment detects changes to:
- Source photos
- Processing settings (`TIMESTAMP_OFFSET_HOURS`, `TARGET_TIMEZONE_OFFSET_HOURS`)
- EXIF modification logic

## Troubleshooting

### Common Issues

**"Mock object is not iterable" error:**
- Ensure `OUTPUT_DIR` is set to a valid Path object in settings
- Check that static site directory exists

**Metadata loading failures:**
- Run `process-photos` command first to generate metadata
- Verify `prod/pics/gallery-metadata.json` exists and is valid JSON

**S3 connection errors:**
- Verify S3 credentials and endpoint configuration
- Check network connectivity and bucket permissions
- Ensure bucket exists and is accessible

### Debug Information

Use `--dry-run` to diagnose deployment issues without uploading:

```bash
python manage.py deploy --dry-run --photos-only
```

This shows:
- Which deployment mode is being used
- Deployment plan details
- Configuration validation results

## See Also

- **[Settings System](../settings.md)**: S3 configuration options
- **[Architecture](../architecture/metadata-consistency.md)**: Metadata consistency system
- **[Services](../services/README.md)**: Deployment orchestration internals