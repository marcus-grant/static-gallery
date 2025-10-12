# Future Enhancements (Post-MVP)

## File Processing Options

### Copy vs Symlink Setting
- Add setting/CLI argument/environment variable to choose between copying or symlinking original files
- Default: symlink (current behavior for storage efficiency)
- Option to copy for situations where symlinks aren't suitable (e.g., cross-filesystem operations)

### Remote Storage Support
- S3-compatible object store integration (AWS S3, Hetzner, etc.)
- Direct upload from source to object storage without local intermediate files
- Streaming processing for very large collections
- Multi-threaded/async uploads for performance

### Working Entirely from Remote Storage
- Allow remote object stores to contain the originals (no local storage required)
- Download photos from archive bucket for processing as needed
- Process and upload to public bucket without keeping local copies
- Memory-efficient workflow for constrained environments

### Automated Archive Upload Command
- `upload-originals` command to automate upload from PIC_SOURCE_PATH_FULL
- Preserve original directory structure and filenames in archive
- Skip already uploaded files (idempotent)
- Progress reporting and resumable uploads for large collections
- SHA256 checksum verification for integrity

### Async Photo Processing Pipeline
- Stream photos directly from remote archive storage without full local download
- Process photos one at a time: download → process → upload to public bucket
- Parallel processing: download next photo while current photo processes/uploads
- Memory-efficient handling of 30GB+ collections without local storage requirements
- Progress tracking and resumable processing for interrupted workflows

### Additional Processing Features
- Resume capability for interrupted processing
- Parallel processing of photos
- Progress reporting for large collections
- Dry-run mode to preview operations

### Automated Web-Sized Image Generation
- Create web-sized versions (2048x2048 max JPEG) from originals
- Automatic resizing with quality optimization
- Support for different output formats and compression settings
- Batch processing for large collections
- Note: Currently not needed as photographer provides pre-optimized web versions