# Galleria Changelog

## 2025-09-25

- Implemented hierarchical settings system (CLI > env vars > local > defaults)
- Added GALLERIA_ prefix for all environment variables
- Implemented local settings override via settings.local.py
- Added XDG Base Directory compliance for config and cache directories
- Established test coverage for settings precedence hierarchy
- Started command infrastructure with find-samples command
- Added CLI argument override testing for commands