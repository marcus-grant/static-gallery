# UUID Service Documentation

## Overview

The UUID service provides RFC 9562 compliant UUIDv7 generation for photo 
filenames, ensuring chronological ordering and collision resistance for burst 
mode photography.

## Service Architecture

### Core Components

- **`src/services/uuid_service.py`**: Main service interface for photo UUID 
  generation
- **`src/util/uuidv7.py`**: RFC 9562 compliant UUIDv7 implementation 
  (CPython-based)

### Key Functions

#### `generate_photo_uuid(timestamp, camera_info, filename) -> str`

Generates a Base32-encoded UUIDv7 from photo metadata.

**Parameters:**
- `timestamp` (Optional[datetime]): EXIF timestamp, uses current time if None
- `camera_info` (Dict): Camera metadata (make, model) for future enhancement
- `filename` (str): Original filename for future collision avoidance

**Returns:**
- `str`: 26-character Base32-encoded UUID (vs 36-character hex)

**Example:**
```python
from src.services.uuid_service import generate_photo_uuid
from datetime import datetime

timestamp = datetime(2024, 10, 5, 14, 30, 45)
camera_info = {"make": "Canon", "model": "EOS R5"}
filename = "IMG_001.jpg"

uuid_str = generate_photo_uuid(timestamp, camera_info, filename)
# Returns: "01JAXYZ123ABC456DEF789GHIJK"
```

## Implementation Details

### RFC 9562 Compliance

The implementation follows RFC 9562 specification exactly:

- **48-bit timestamp**: Milliseconds since Unix epoch (not nanoseconds)
- **4-bit version**: Set to 7
- **12-bit rand_a**: High bits of monotonic counter
- **2-bit variant**: Set to 10 (binary)
- **62-bit rand_b**: Low bits of counter + 32-bit random tail

### Burst Mode Handling

For rapid photo captures with identical timestamps:

- **42-bit monotonic counter** across rand_a and rand_b fields
- **Counter increment** for same-millisecond generation
- **Timestamp advancement** on counter overflow
- **Thread-safe** global state management

### Chronological Ordering

UUIDs are k-sortable (chronologically sortable):

```python
# Generate UUIDs with different timestamps
uuid1 = generate_photo_uuid(datetime(2024, 1, 1, 12, 0, 0), {}, "IMG_001.jpg")
uuid2 = generate_photo_uuid(datetime(2024, 1, 1, 12, 0, 1), {}, "IMG_002.jpg")

# Lexicographic sorting maintains chronological order
assert uuid1 < uuid2  # True
```

### Base32 Encoding

UUIDs are encoded in Base32 for shorter, URL-safe filenames:

- **Length**: 26 characters (vs 36 hex with hyphens)
- **Character set**: A-Z, 2-7 (RFC 4648)
- **URL-safe**: No special characters requiring escaping

## Integration Points

### EXIF Processing

```python
# Convert EXIF datetime to milliseconds for RFC compliance
if timestamp:
    timestamp_ms = int(timestamp.timestamp() * 1000)
    photo_uuid = uuid7(timestamp_ms)
else:
    photo_uuid = uuid7()
```

### Photo Processing Pipeline

The service integrates with the broader photo processing workflow:

1. **EXIF extraction** → datetime object
2. **UUID generation** → chronologically ordered identifier
3. **File renaming** → `{uuid}.jpg`, `{uuid}.webp`
4. **Storage upload** → Hetzner buckets with UUID keys

## Testing

### Test Coverage

- **`test/test_uuid_service.py`**: Service interface tests
- **`test/test_uuidv7.py`**: Comprehensive UUIDv7 implementation tests

### Test Categories

1. **RFC 9562 Compliance**: Field layout, version/variant bits, millisecond 
   precision
2. **Burst Mode**: Same-millisecond uniqueness, counter increment, overflow 
   handling
3. **Thread Safety**: Concurrent generation, shared state protection
4. **Chronological Ordering**: K-sortable verification, mixed timestamp 
   handling

### Example Test

```python
def test_generate_photo_uuid_basic():
    timestamp = datetime(2024, 10, 5, 14, 30, 45)
    camera_info = {"make": "Canon", "model": "EOS R5"}
    filename = "IMG_001.jpg"
    
    photo_uuid = generate_photo_uuid(timestamp, camera_info, filename)
    
    assert isinstance(photo_uuid, str)
    assert len(photo_uuid) == 26
    assert all(c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567" for c in photo_uuid)
```

## Future Enhancements

### Camera Info Integration

The `camera_info` parameter is prepared for future collision avoidance:

- Incorporate camera make/model into random bits
- Reduce collision probability for multi-camera shoots
- Maintain RFC 9562 compliance

### Filename Integration

The `filename` parameter supports future enhancements:

- Hash original filename into random portion
- Handle filename rollover edge cases
- Preserve original naming context

## Migration Notes

### Python 3.14+ Transition

When Python 3.14+ becomes available:

1. Remove `src/util/uuidv7.py`
2. Update imports to use `uuid.uuid7()` from standard library
3. Verify timestamp handling remains millisecond-based
4. Test chronological ordering preservation
5. Update documentation references

### Dependencies

Current implementation removes dependency on:

- **`uuid7`** package (non-compliant with RFC 9562)
- **`uuid-extensions`** package (import mismatch)

Uses only Python standard library plus:

- **`secrets`** for cryptographically secure randomness
- **`threading`** for thread-safe counter management