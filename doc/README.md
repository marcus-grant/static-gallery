# Galleria Documentation

Welcome to the Galleria documentation. This directory contains comprehensive 
documentation for the wedding photo gallery system.

## Overview

Galleria is a static wedding photo gallery built with Pelican, using AlpineJS 
for frontend interactions and Tailwind CSS for styling. Photos are processed 
with UUIDv7-based filenames derived from EXIF data and hosted on Hetzner 
object storage with BunnyCDN for global distribution.

**Priority**: Speed of development and deployment over feature richness. Get a 
working, acceptable user experience deployed quickly.

## Documentation Index

### Configuration & Settings
- **[Settings System](./settings.md)** - Complete guide to Galleria's 
  hierarchical settings system, environment variables, local settings, and XDG 
  compliance

### Development & Architecture
- **[Development Specification](./TODO.md)** - Detailed development tasks, 
  specifications, and project roadmap
- **[Changelog](./CHANGELOG.md)** - Record of completed features and major 
  changes
- **[Contributing Guidelines](./CONTRIBUTE.md)** - Development workflow, testing requirements, and commit conventions

### Testing Infrastructure
- **[Testing Documentation](./testing/README.md)** - Test fixtures, isolation patterns, and synthetic photo generation for reproducible CI/CD-compatible testing

### Command-Line Interface
- **[Command Documentation](./command/README.md)** - Complete guide to all CLI 
  commands including usage examples, options, and workflows

### Architecture & Implementation  
- **[Static Site Generation](./architecture/static-site-generation.md)** - Template system, build process, and development server
- **[Services Documentation](./services/README.md)** - Service layer components and core business logic implementations

### Utilities & Implementation Notes
- **[UUIDv7 Implementation](./util/UUIDv7.md)** - RFC 9562 compliance, Python 
  standard library status, and implementation strategy for chronological photo IDs

### Getting Started
- **[Main README](../README.md)** - Project overview, setup instructions, and 
  basic usage

## Quick Reference

### Key Concepts
- **Settings Hierarchy**: CLI args > env vars > local settings > defaults
- **Environment Variables**: All use `GALLERIA_` prefix
- **Local Settings**: Override defaults via `settings.local.py`
- **XDG Compliance**: Respects `XDG_CONFIG_HOME` and `XDG_CACHE_HOME`

### Technology Stack
- **Backend**: Python 3.12, Pelican static generator
- **Frontend**: AlpineJS + Tailwind CSS (CDN, no build step)
- **Photo Processing**: Pillow, exifread, RFC 9562 UUIDv7 naming
- **Storage**: Hetzner object storage with BunnyCDN
- **Testing**: pytest with pyfakefs for filesystem mocking

## Contributing

When adding new documentation:
1. Create focused, single-purpose documents
2. Update this index with appropriate links
3. Follow existing markdown formatting conventions
4. Keep technical details in specific documents, overviews here