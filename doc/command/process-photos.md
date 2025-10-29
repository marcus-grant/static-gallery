# process-photos Command

The `process-photos` command processes original photo collections into web-ready formats with chronological filenames, batch processing support, and crash recovery capabilities.

## Overview

This command reads full resolution and web-optimized photo collections, generates chronological filenames based on EXIF timestamps, creates symlinks and thumbnails, and produces gallery metadata with full batch processing and recovery support.

## Usage

```bash
python manage.py process-photos [OPTIONS]
```

## Options

### Source Directories
- `--full-source`, `-f` PATH - Full resolution photo directory (defaults to `PIC_SOURCE_PATH_FULL`)
- `--web-source`, `-w` PATH - Web-optimized photo directory (defaults to `PIC_SOURCE_PATH_WEB`)
- `--output`, `-o` PATH - Output directory (defaults to `prod/pics`)

### Collection Settings  
- `--collection-name`, `-c` TEXT - Name for this photo collection (default: "wedding")

### Processing Options
- `--skip-validation` - Skip validation and process only matching photos
- `--dry-run` - Show what would be processed without actually doing it
- `--batch-size` INTEGER - Photos per batch for processing (default: 50)

### Recovery Options (NEW)
- `--resume` - Resume from partial files left by previous incomplete processing
- `--restart` - Clean partial files and restart processing from scratch

## Features

### Progress Reporting
Real-time progress output during processing:
```
Processing batch 1, photos 1-50
Processing photo 1/645: IMG_001.jpg
Processing photo 2/645: IMG_002.jpg
...
```

### Batch Processing with Crash Recovery
- Processes photos in configurable batches (default: 50 photos)
- Creates partial metadata files after each batch: `gallery-metadata.part001.json`, `gallery-metadata.part002.json`, etc.
- Enables recovery from interruptions without reprocessing completed batches

### Automatic Partial File Detection
If partial files exist from previous incomplete runs:
```bash
Error: Partial files detected from previous incomplete processing:
  - gallery-metadata.part001.json
  - gallery-metadata.part002.json

Use --resume to continue from partial files or --restart to clean and start over.
```

## Examples

### Basic Processing
```bash
# Process default directories
python manage.py process-photos

# Process specific directories
python manage.py process-photos \
  --full-source /path/to/full/photos \
  --web-source /path/to/web/photos \
  --output /path/to/output
```

### Crash Recovery
```bash
# Resume from previous incomplete processing
python manage.py process-photos --resume

# Clean partial files and start fresh
python manage.py process-photos --restart

# Custom batch size for memory management
python manage.py process-photos --batch-size 25
```

### Development Workflow
```bash
# Dry run to see what would be processed
python manage.py process-photos --dry-run

# Skip validation for mismatched collections
python manage.py process-photos --skip-validation

# Process sample photos for testing
python manage.py process-photos \
  --full-source ./test-photos/full \
  --web-source ./test-photos/web \
  --collection-name test-collection
```

## Output Structure

The command creates this directory structure:

```
output_directory/
├── full/                    # Symlinks to full resolution photos
│   ├── wedding-20231015T143022.450+0200-Canon-0.jpg
│   └── wedding-20231015T143023.100+0200-Canon-1.jpg
├── web/                     # Symlinks to web-optimized photos  
│   ├── wedding-20231015T143022.450+0200-Canon-0.jpg
│   └── wedding-20231015T143023.100+0200-Canon-1.jpg
├── thumb/                   # Generated WebP thumbnails
│   ├── wedding-20231015T143022.450+0200-Canon-0.webp
│   └── wedding-20231015T143023.100+0200-Canon-1.webp
├── gallery-metadata.json    # Final complete metadata
├── gallery-metadata.part001.json  # Partial metadata (if batch processing)
└── gallery-metadata.part002.json  # Partial metadata (if batch processing)
```

## Batch Processing Details

### How Batches Work
1. Photos are processed in groups of `--batch-size` (default: 50)
2. After each batch completion, a partial metadata file is saved
3. Partial files contain metadata for all photos processed so far
4. Final `gallery-metadata.json` contains complete metadata

### Recovery Process
- **Resume**: Continues processing from where the last batch left off
- **Restart**: Deletes all partial files and starts fresh processing
- **Automatic Detection**: Command fails if partial files exist without recovery flag

### Partial File Format
Partial files follow the naming pattern: `gallery-metadata.part{batch:03d}.json`
- `gallery-metadata.part001.json` - First batch (photos 1-50)
- `gallery-metadata.part002.json` - Second batch (photos 1-100) 
- etc.

## Integration with Other Commands

### Before build
```bash
python manage.py process-photos
python manage.py build
```

### Complete pipeline
```bash
python manage.py process-photos
python manage.py build  
python manage.py deploy
```

## Error Handling

### Collection Validation Errors
```bash
Error: Collections don't match perfectly.
Use --skip-validation to process only matching photos.
```

### Partial File Conflicts
```bash
Error: Partial files detected from previous incomplete processing:
  - gallery-metadata.part001.json

Use --resume to continue from partial files or --restart to clean and start over.
```

### Missing Directories
```bash
Error: Full resolution directory does not exist: /path/to/missing
```

## Performance

- **Current Performance**: ~12.7 seconds for 50 photos
- **Batch Processing**: Reduces memory usage for large collections (645+ photos)
- **Progress Reporting**: Real-time feedback for long-running operations
- **Recovery**: Avoids reprocessing hundreds of photos after interruption

## Configuration

The command uses these settings:
- `PIC_SOURCE_PATH_FULL` - Default full resolution source directory
- `PIC_SOURCE_PATH_WEB` - Default web-optimized source directory  
- `TIMESTAMP_OFFSET_HOURS` - Camera time correction offset
- `TARGET_TIMEZONE_OFFSET_HOURS` - Target timezone for EXIF correction

## Related Documentation

- [File Processing Service](../services/file_processing.md) - Implementation details
- [deploy Command](deploy.md) - Next step in the pipeline
- [Settings](../settings.md) - Configuration options