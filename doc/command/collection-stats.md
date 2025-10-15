# collection-stats Command

Analyze photo collections for timing patterns, file sizes, camera information, and timezone data. This command helps identify camera synchronization issues, storage requirements, and photographer patterns.

## Usage

```bash
python manage.py collection-stats [OPTIONS]
```

## Options

- `--full-source`, `-f` - Full resolution photo directory (overrides `PIC_SOURCE_PATH_FULL`)
- `--web-source`, `-w` - Web-optimized photo directory (overrides `PIC_SOURCE_PATH_WEB`) 
- `--processed`, `-p` - Processed photos directory (overrides `prod/pics`)

## Output Sections

### Original Collections Analysis
- Photo counts and total file sizes
- File size statistics (average, median, min/max ranges)
- Storage requirements for full and web-optimized versions

### Processed Collection Analysis  
- Symlink counts for full and web directories
- Generated thumbnail sizes and counts
- Verification that processing completed successfully

### Time Analysis
- Photo timeline (earliest, latest, median timestamps)
- Total shooting duration
- Average time intervals between photos
- Longest gaps (useful for identifying breaks/events)
- Timezone information from EXIF data

### Camera & Photographer Analysis
- Filename patterns (identifies different cameras/photographers)
- Camera models from EXIF data
- Distribution analysis across multiple photographers

## Example Output

```
=== PHOTO COLLECTION ANALYSIS ===

ORIGINAL COLLECTIONS:
Full Resolution: 645 photos
  Total size: 21.2 GB
  Average size: 33.6 MB
  Median size: 30.0 MB
  Size range: 11.5 MB - 70.4 MB

TIME ANALYSIS:
Earliest photo: 2025-08-09 13:20:34
Latest photo: 2025-08-09 23:19:20
Total duration: 9:58:46
Average time between photos: 55.8 seconds

TIMEZONE INFORMATION:
  +00:00: 645 photos (100.0%)

FILENAME PATTERNS:
  5W*: 742 photos
  4F*: 548 photos
```

## Use Cases

### Camera Synchronization Issues
Identify timing discrepancies between multiple cameras:
- Different timezone settings
- Manual clock errors  
- Systematic offsets requiring correction

### Storage Planning
Calculate storage requirements:
- Archive storage needs
- CDN bandwidth estimates
- Thumbnail generation costs

### Wedding Timeline Analysis
Understand event flow:
- Actual shooting duration vs. planned time
- Break periods and event transitions
- Photographer coverage patterns

### Multi-Photographer Workflows
Analyze coverage from multiple photographers:
- Photo distribution between cameras
- Filename pattern identification
- Coverage overlap analysis

## Troubleshooting

**No photos found**: Check that source directories exist and contain image files (.jpg, .jpeg)

**No EXIF timestamps**: Some cameras don't embed timestamp data - check camera settings

**Incorrect timezone data**: Camera timezone settings may not match actual shooting location

**Memory usage**: Large collections (1000+ photos) may take several minutes to analyze

## Related Commands

- **process-photos** - Process collections after analyzing them
- **find-samples** - Get sample photos for testing analysis
- **build** - Generate gallery after understanding collection characteristics