# Personal Wedding Gallery Setup Notes

**Collection**: Wedding photos from August 9th, 2025 in Sweden
**Total Photos**: 645 photos from dual Canon EOS R5 setup

## EXIF Timezone Analysis & Configuration

### Camera Timezone Issue Discovery

**Problem**: Camera recorded correct Swedish local time but marked timezone incorrectly as UTC (+00:00) instead of Swedish summer time (+02:00).

**Evidence from EXIF analysis**:
- Photo 5W9A2613.JPG: Shows 16:10:04 with +00:00 timezone 
- Photo 5W9A3782.JPG: Shows 18:31:04 with +00:00 timezone
- Ceremony started at 16:00 Swedish time - timeline matches perfectly
- GNOME image viewer shows 18:10 and 20:31 respectively (adding local timezone offset)

**Timeline Verification**: Photos span complete wedding day:
- **First photo**: 13:20:34 (preparation)
- **Ceremony start**: ~16:00 (ceremony photos at 16:10)
- **Last photo**: 23:19:20 (late evening celebration)
- **Total duration**: ~10 hours of coverage

### Correct Settings Determined

```python
# settings.local.py configuration
TIMESTAMP_OFFSET_HOURS = 0  # Camera time was correct local time
TARGET_TIMEZONE_OFFSET_HOURS = 2  # Swedish summer time (CEST = UTC+2)
```

**Logic**: 
- Keep original times (16:10, 18:31) as they represent correct Swedish local time
- Fix EXIF timezone from +00:00 to +02:00 during deployment
- This prevents timezone conversion issues in photo viewers

### Collection Paths

```python
PIC_SOURCE_PATH_FULL = Path("/home/marcus/Pictures/wedding/full")
PIC_SOURCE_PATH_WEB = Path("/home/marcus/Pictures/wedding/web") 
```

### S3 Production Configuration

```python
# Environment variables set in profile
HETZNER_GALLERIA_WEDDING_PROD_ENDPOINT="https://bucket-name.region.hetznerobjects.com"
HETZNER_GALLERIA_WEDDING_PROD_ACCESS_KEY="access_key"
HETZNER_MAIN_BUCKETS_PRIVATE_KEY="secret_key"

# settings.local.py
S3_PUBLIC_ENDPOINT = getenv("HETZNER_GALLERIA_WEDDING_PROD_ENDPOINT")
S3_PUBLIC_ACCESS_KEY = getenv("HETZNER_GALLERIA_WEDDING_PROD_ACCESS_KEY") 
S3_PUBLIC_SECRET_KEY = getenv("HETZNER_MAIN_BUCKETS_PRIVATE_KEY")
S3_PUBLIC_REGION = "eu-central-1"
```