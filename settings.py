import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


BASE_DIR = Path(__file__).resolve().parent

# Default settings - will be overridden by local settings then env vars
PIC_SOURCE_PATH_FULL = BASE_DIR / 'pics'
OUTPUT_DIR = BASE_DIR / 'output'
PROCESSED_DIR = BASE_DIR / 'processed-photos'

# Pelican settings
CONTENT_DIR = BASE_DIR / 'content'
THEME_DIR = BASE_DIR / 'themes' / 'wedding'

# XDG directories
CONFIG_DIR = BASE_DIR  # Default to project root
if 'XDG_CONFIG_HOME' in os.environ:
    CONFIG_DIR = Path(os.environ['XDG_CONFIG_HOME']) / 'galleria'

LOCAL_SETTINGS_FILENAME = os.getenv('GALLERIA_LOCAL_SETTINGS_FILENAME', 'settings.local.py')

CACHE_DIR = BASE_DIR / 'cache'
if 'XDG_CACHE_HOME' in os.environ:
    CACHE_DIR = Path(os.environ['XDG_CACHE_HOME']) / 'galleria'

# Ensure directories exist
CACHE_DIR.mkdir(parents=True, exist_ok=True)
PIC_SOURCE_PATH_FULL.mkdir(parents=True, exist_ok=True)

# Photo processing settings
WEB_SIZE = (2048, 2048)  # Max dimensions for web version
THUMB_SIZE = (400, 400)  # Max dimensions for thumbnails
JPEG_QUALITY = 85
WEBP_QUALITY = 85

# Load local settings if present
LOCAL_SETTINGS_PATH = CONFIG_DIR / LOCAL_SETTINGS_FILENAME
if LOCAL_SETTINGS_PATH.exists():
    # Read and execute the local settings file
    local_namespace = {}
    with open(LOCAL_SETTINGS_PATH, 'r') as f:
        exec(f.read(), local_namespace)
    
    # Import all ALL_CAPS settings from local namespace
    for attr, value in local_namespace.items():
        if attr.isupper() and not attr.startswith('_'):
            globals()[attr] = value
            # For Path variables, ensure they stay as Path objects
            if attr.endswith('_PATH') or attr.endswith('_DIR'):
                if not isinstance(value, Path):
                    globals()[attr] = Path(value)

# Apply environment variable overrides after local settings
PIC_SOURCE_PATH_FULL = Path(os.getenv('GALLERIA_PIC_SOURCE_PATH_FULL', str(PIC_SOURCE_PATH_FULL)))
OUTPUT_DIR = Path(os.getenv('GALLERIA_OUTPUT_DIR', str(OUTPUT_DIR)))
PROCESSED_DIR = Path(os.getenv('GALLERIA_PROCESSED_DIR', str(PROCESSED_DIR)))

# TODO: Consider adding TEST_OUTPUT_PATH setting for real-world testing
# This would allow test outputs to be separate from production processing paths
# TEST_OUTPUT_PATH = Path(os.getenv('GALLERIA_TEST_OUTPUT_PATH', str(BASE_DIR / 'test-output')))