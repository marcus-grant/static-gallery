# EXIF Modification Service

The EXIF modification service provides in-memory EXIF metadata modification for deployment-ready photo processing, supporting dual timezone handling and hash-based change detection.

## Overview

The `modify_exif_in_memory()` function in `src/services/s3_storage.py` enables real-time EXIF modification during deployment without temporary file creation, supporting the dual-hash metadata system for selective deployment.

## Dual Timezone System

### Settings Configuration

Two settings control timezone handling:

- **`TIMESTAMP_OFFSET_HOURS`**: Corrects systematic camera time errors
  - Example: Camera was set 2 hours fast → offset = -2 to correct
  - Applied during photo processing phase

- **`TARGET_TIMEZONE_OFFSET_HOURS`**: Sets timezone context for deployment
  - Writes timezone info to EXIF `OffsetTimeOriginal` field per EXIF 2.31 standard
  - Format: `±HH:MM` (e.g., `-05:00` for EST, `+02:00` for CET)
  - Special value 13 = preserve original timezone (don't modify `OffsetTimeOriginal`)

### Combined Logic

```
Raw EXIF timestamp + TIMESTAMP_OFFSET_HOURS = Corrected timestamp
Corrected timestamp + TARGET_TIMEZONE_OFFSET_HOURS → EXIF OffsetTimeOriginal
```

**Example:**
- Raw EXIF: `2023-12-25 15:30:00` (no timezone info)
- `TIMESTAMP_OFFSET_HOURS = -2` (camera was 2 hours fast)
- `TARGET_TIMEZONE_OFFSET_HOURS = -5` (deploying for EST timezone)

**Result:**
- Corrected timestamp: `2023-12-25 13:30:00`
- Deployed EXIF: `DateTimeOriginal: 2023-12-25 13:30:00` + `OffsetTimeOriginal: -05:00`
- **Meaning**: Photo was taken at 1:30 PM Eastern Standard Time

## Function Reference

### `modify_exif_in_memory(image_bytes, corrected_timestamp, target_timezone_offset_hours)`

Modifies EXIF data in memory with corrected timestamp and timezone.

**Parameters:**
- `image_bytes` (bytes): Original image data as bytes
- `corrected_timestamp` (datetime): Corrected timestamp to set in DateTimeOriginal
- `target_timezone_offset_hours` (int): Target timezone offset in hours (13 = preserve original)

**Returns:**
- `bytes`: Modified image bytes with updated EXIF data

**EXIF 2.31 Compliance:**
- Updates `DateTimeOriginal` with corrected timestamp
- Sets `OffsetTimeOriginal` in `±HH:MM` format
- Preserves all other EXIF data and image quality

## Integration with Dual-Hash System

The EXIF modification function enables accurate `deployment_file_hash` calculation:

1. **Photo Processing Phase**: Calculate both `file_hash` (original) and `deployment_file_hash` (after EXIF modification simulation)
2. **Deployment Phase**: Only upload photos where `deployment_file_hash` differs from remote state
3. **Settings Changes**: Changing either timezone setting triggers new deployment hashes

For complete details on how this integrates with the metadata consistency system, see **[Metadata Consistency System](../architecture/metadata-consistency.md)**.

## Testing

Comprehensive test suite in `test/services/test_s3_storage.py::TestExifModification`:

- Timestamp correction functionality
- Timezone offset formatting (`±HH:MM`)
- Special value handling (offset 13)
- EXIF data preservation
- Image quality preservation
- Hash differentiation with different settings

## Error Handling

- Handles images without existing EXIF data
- Creates minimal EXIF structure when none exists
- Preserves image quality during modification
- Maintains EXIF 2.31 standard compliance