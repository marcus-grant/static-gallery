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

### Additional Processing Features
- Resume capability for interrupted processing
- Parallel processing of photos
- Progress reporting for large collections
- Dry-run mode to preview operations