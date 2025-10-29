# Command Documentation

This directory contains detailed documentation for Galleria's command-line interface. Each command is documented with usage examples, options, and common workflows.

## Available Commands

### Analysis & Development

- **[collection-stats](collection-stats.md)** - Analyze photo collections for timing, file sizes, and camera patterns

### Photo Processing

- **find-samples** - Find sample photos for testing and development
- **process-photos** - Process original photos into web-ready formats with chronological filenames
- **upload-photos** - Upload processed photos to cloud storage

### Site Generation & Deployment

- **build** - Generate static website from processed photos
- **serve** - Development server with hot-reload for template development
- **[deploy](deploy.md)** - Deploy complete gallery to production hosting with metadata-driven optimization and automatic CORS configuration

## Command Categories

### Development Workflow
```bash
# Analyze your photo collection
python manage.py collection-stats

# Process photos for development
python manage.py process-photos --source ./sample-photos

# Build and serve locally
python manage.py build
python manage.py serve --reload
```

### Production Workflow
```bash
# Full production pipeline
python manage.py process-photos
python manage.py build
python manage.py deploy
```

## Getting Help

For detailed help on any command:
```bash
python manage.py COMMAND --help
```

For general help:
```bash
python manage.py --help
```

## Contributing

When adding new commands, please:
1. Add documentation in this directory following the naming pattern `command-name.md`
2. Update this README with the new command
3. Include usage examples and common use cases
4. Document all CLI options and their purposes