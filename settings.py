import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


BASE_DIR = Path(__file__).resolve().parent

# Default settings - will be overridden by local settings then env vars
PIC_SOURCE_PATH_FULL = BASE_DIR / 'pics'
PIC_SOURCE_PATH_WEB = BASE_DIR / 'pics-web'  # Web-optimized versions from photographer
OUTPUT_DIR = BASE_DIR / 'output'

# Pelican settings
CONTENT_DIR = BASE_DIR / 'content'
THEME_DIR = BASE_DIR / 'themes' / 'wedding'

# S3-Compatible Storage Configuration Defaults
# These have no sane defaults - must be configured per deployment
# Private archive bucket (for original photos - manual upload)
S3_ARCHIVE_ENDPOINT = None  # e.g., 'eu-central-1.s3.hetznerobjects.com'
S3_ARCHIVE_ACCESS_KEY = None
S3_ARCHIVE_SECRET_KEY = None
S3_ARCHIVE_BUCKET = None  # Your private bucket name
S3_ARCHIVE_REGION = None  # e.g., 'eu-central-1'

# Public gallery bucket (for processed photos - automated upload)
S3_PUBLIC_ENDPOINT = None  # e.g., 'eu-central-1.s3.hetznerobjects.com'
S3_PUBLIC_ACCESS_KEY = None
S3_PUBLIC_SECRET_KEY = None
S3_PUBLIC_BUCKET = None  # Your public bucket name
S3_PUBLIC_REGION = None  # e.g., 'eu-central-1'

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

# EXIF timestamp correction settings
TIMESTAMP_OFFSET_HOURS = 0  # Offset to correct systematic timestamp errors (hours)
TARGET_TIMEZONE_OFFSET_HOURS = 13  # Target timezone for EXIF deployment (13 = preserve original)

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
PIC_SOURCE_PATH_WEB = Path(os.getenv('GALLERIA_PIC_SOURCE_PATH_WEB', str(PIC_SOURCE_PATH_WEB)))
OUTPUT_DIR = Path(os.getenv('GALLERIA_OUTPUT_DIR', str(OUTPUT_DIR)))

# S3 settings - environment variable overrides
S3_ARCHIVE_ENDPOINT = os.getenv('GALLERIA_S3_ARCHIVE_ENDPOINT', S3_ARCHIVE_ENDPOINT)
S3_ARCHIVE_ACCESS_KEY = os.getenv('GALLERIA_S3_ARCHIVE_ACCESS_KEY', S3_ARCHIVE_ACCESS_KEY)
S3_ARCHIVE_SECRET_KEY = os.getenv('GALLERIA_S3_ARCHIVE_SECRET_KEY', S3_ARCHIVE_SECRET_KEY)
S3_ARCHIVE_BUCKET = os.getenv('GALLERIA_S3_ARCHIVE_BUCKET', S3_ARCHIVE_BUCKET)
S3_ARCHIVE_REGION = os.getenv('GALLERIA_S3_ARCHIVE_REGION', S3_ARCHIVE_REGION)

S3_PUBLIC_ENDPOINT = os.getenv('GALLERIA_S3_PUBLIC_ENDPOINT', S3_PUBLIC_ENDPOINT)
S3_PUBLIC_ACCESS_KEY = os.getenv('GALLERIA_S3_PUBLIC_ACCESS_KEY', S3_PUBLIC_ACCESS_KEY)
S3_PUBLIC_SECRET_KEY = os.getenv('GALLERIA_S3_PUBLIC_SECRET_KEY', S3_PUBLIC_SECRET_KEY)
S3_PUBLIC_BUCKET = os.getenv('GALLERIA_S3_PUBLIC_BUCKET', S3_PUBLIC_BUCKET)
S3_PUBLIC_REGION = os.getenv('GALLERIA_S3_PUBLIC_REGION', S3_PUBLIC_REGION)

# EXIF timestamp correction - environment variable override
TIMESTAMP_OFFSET_HOURS = int(os.getenv('GALLERIA_TIMESTAMP_OFFSET_HOURS', str(TIMESTAMP_OFFSET_HOURS)))
TARGET_TIMEZONE_OFFSET_HOURS = int(os.getenv('GALLERIA_TARGET_TIMEZONE_OFFSET_HOURS', str(TARGET_TIMEZONE_OFFSET_HOURS)))

# TODO: Consider adding TEST_OUTPUT_PATH setting for real-world testing
# This would allow test outputs to be separate from production processing paths
# TEST_OUTPUT_PATH = Path(os.getenv('GALLERIA_TEST_OUTPUT_PATH', str(BASE_DIR / 'test-output')))

