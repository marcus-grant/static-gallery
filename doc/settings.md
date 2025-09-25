# Settings System

Galleria uses a hierarchical settings system with clear precedence order for configuration values.

## Settings Hierarchy

Override precedence from highest to lowest:

1. **CLI arguments** (not yet implemented)
2. **Environment variables** (GALLERIA_* prefix)  
3. **Local settings file** (settings.local.py)
4. **Default settings** (settings.py)

## Environment Variables

All environment variables must use the `GALLERIA_` prefix followed by the setting name:

- `GALLERIA_PIC_SOURCE_PATH_FULL` → overrides `PIC_SOURCE_PATH_FULL`
- `GALLERIA_OUTPUT_DIR` → overrides `OUTPUT_DIR`
- `GALLERIA_PROCESSED_DIR` → overrides `PROCESSED_DIR`
- `GALLERIA_LOCAL_SETTINGS_FILENAME` → overrides local settings filename

## Local Settings File

Override defaults without modifying settings.py:

- **Default location**: `{project_root}/settings.local.py`
- **Configurable via**: `GALLERIA_LOCAL_SETTINGS_FILENAME`
- **XDG location**: Uses `~/.config/galleria/` if `XDG_CONFIG_HOME` is set
- **Format**: Valid Python with ALL_CAPS variables

### Example settings.local.py

```python
from pathlib import Path

# Override photo source directory
PIC_SOURCE_PATH_FULL = Path('/custom/photos/path')

# Override image processing settings  
WEB_SIZE = (1920, 1080)
JPEG_QUALITY = 90
```

## XDG Compliance

- **CONFIG_DIR**: `$XDG_CONFIG_HOME/galleria` or `{project_root}`
- **CACHE_DIR**: `$XDG_CACHE_HOME/galleria` or `{project_root}/cache`

## Key Settings

### Photo Processing
- `PIC_SOURCE_PATH_FULL`: Source photo directory (default: `{project}/pics`)
- `OUTPUT_DIR`: Generated site output (default: `{project}/output`)
- `PROCESSED_DIR`: Processed photos (default: `{project}/processed-photos`)
- `WEB_SIZE`: Web-optimized dimensions (default: `(2048, 2048)`)
- `THUMB_SIZE`: Thumbnail dimensions (default: `(400, 400)`)
- `JPEG_QUALITY`: JPEG compression (default: `85`)
- `WEBP_QUALITY`: WebP compression (default: `85`)

### Pelican
- `CONTENT_DIR`: Pelican content directory
- `THEME_DIR`: Custom theme location

### Local Settings
- `LOCAL_SETTINGS_FILENAME`: Local settings filename (default: `settings.local.py`)