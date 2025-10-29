# Services Documentation

This directory contains documentation for Galleria's service layer components and utilities.

## Services

- **[File Processing Service](file_processing.md)** - Central photo collection processing with dual-hash metadata and incremental updates
- **[Deployment Service](deployment.md)** - Metadata-driven deployment orchestration with atomic operations, hash-based change detection, and CORS validation
- **[S3 Storage Service](s3_storage.md)** - S3-compatible cloud storage operations with streaming uploads, in-memory EXIF modification, and CORS management
- **[UUID Service](uuid_service.md)** - Photo UUID generation with RFC 9562 UUIDv7, Base32 encoding, and chronological ordering
- **[EXIF Modification Service](exif_modification.md)** - In-memory EXIF modification with dual timezone handling and deployment hash calculation

## Overview

Service documentation covers the implementation details, APIs, and usage patterns for Galleria's core services. Each service document includes purpose, implementation approach, and integration guidelines.

## Contributing

When adding new service documentation:
1. Document the service's purpose and responsibilities
2. Include API details and usage examples
3. Cover implementation decisions and trade-offs
4. Update this README with new services