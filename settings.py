import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


BASE_DIR = Path(__file__).resolve().parent

# Photo source directories
PIC_SOURCE_PATH_FULL = Path(os.getenv('GALLERIA_PIC_SOURCE_PATH_FULL', str(BASE_DIR / 'sample-pics')))

# Output directories
OUTPUT_DIR = Path(os.getenv('OUTPUT_DIR', str(BASE_DIR / 'output')))
PROCESSED_DIR = Path(os.getenv('PROCESSED_DIR', str(BASE_DIR / 'processed-photos')))

# Pelican settings
CONTENT_DIR = BASE_DIR / 'content'
THEME_DIR = BASE_DIR / 'themes' / 'wedding'

# Cache directory (XDG compliant)
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
try:
    from settings.local import *
except ImportError:
    pass