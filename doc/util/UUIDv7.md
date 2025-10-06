# UUIDv7 Implementation Guide

## Overview

UUIDv7 is a time-ordered UUID variant defined in RFC 9562 (published May 2024)
that supersedes RFC 4122.
It provides chronological ordering (k-sortable) while
maintaining collision resistance,
making it ideal for photo filename generation where
chronological order is critical.

## RFC 9562 Specification

### Official Definition

**Source**: [RFC 9562 - Section 5.7](https://www.rfc-editor.org/rfc/rfc9562.html#section-5.7)

UUIDv7 features a time-ordered value field derived from
the Unix Epoch timestamp source
(milliseconds since midnight 1 Jan 1970 UTC, leap seconds excluded).
It has improved entropy characteristics over UUIDv1 and UUIDv6.

### Field Layout

```txt
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                           unix_ts_ms                          |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|          unix_ts_ms           |  ver  |       rand_a          |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|var|                        rand_b                             |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                            rand_b                             |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

#### Field Descriptions

- **unix_ts_ms** (48 bits):
  - Big-endian unsigned number of Unix Epoch timestamp in **milliseconds**
- **ver** (4 bits):
  - Version field set to `0b0111` (7)
- **rand_a** (12 bits):
  - Pseudorandom data and/or optional constructs for monotonicity
- **var** (2 bits):
  - Variant field set to `0b10`
- **rand_b** (62 bits):
  - Pseudorandom data and/or optional counter for monotonicity

### Key Specifications

1. **Timestamp Precision**: **Milliseconds** since Unix epoch (not nanoseconds)
2. **Total Random Bits**: 74 bits (rand_a + rand_b) available for randomness/counters
3. **Monotonicity Options**: Implementations MAY use counters in
    random fields for monotonicity within same millisecond
4. **Chronological Ordering**: UUIDs sort chronologically (k-sortable)

## Python Standard Library Status

### Current Implementation

**Source**: [CPython Pull Request #121119](https://github.com/python/cpython/pull/121119)

Python's UUIDv7 implementation is available in Python 3.14+
(currently in development).
The implementation uses:

- 48-bit millisecond timestamp
- 42-bit monotonic counter across rand_a and rand_b fields
- 32-bit random tail
- Global state for counter persistence

### Implementation Approach

```python
def uuid7(timestamp_ms: Optional[int] = None) -> uuid.UUID:
    """Generate UUID version 7 per RFC 9562."""
    # Uses millisecond timestamp + 42-bit counter + 32-bit random
    # Provides monotonicity within same millisecond
    # Auto-increments timestamp if counter overflows
```

### Migration Path

**Current Status**: Python 3.12 does not include UUIDv7
**Future**: Python 3.14+ will include `uuid.uuid7()` in standard library
**Action Required**: Remove custom implementation when upgrading to Python 3.14+

## Third-Party Package Issues

### uuid7 Package (PyPI)

**Package**: `uuid7==0.1.0` on PyPI  
**Status**: **Non-compliant with RFC 9562**  
**Issues**:

- Uses **nanoseconds** instead of RFC-mandated **milliseconds**
- Based on obsolete draft specifications
- Incompatible with final RFC 9562 standard

**Recommendation**: **Do not use** - implement RFC-compliant version instead

### Alternative Packages

- **uuid6**: Claims RFC 9562 compliance, worth evaluating
- **uuid-extension**: Another RFC 9562 implementation
- **Custom implementation**: Copy CPython's implementation (preferred for control)

## Implementation Status for Galleria

### Completed Implementation

**Status**: **IMPLEMENTED** (October 2024)

All requirements have been successfully implemented:

1. **Chronological Ordering**: RFC 9562 compliant k-sortable UUIDs
2. **Burst Mode Handling**: 42-bit monotonic counter for same-millisecond photos
3. **EXIF Timestamp Integration**: Datetime to milliseconds conversion
4. **Base32 Encoding**: 26-character filenames vs 36-character hex

### Implementation Files

- **`src/util/uuidv7.py`**: RFC 9562 compliant UUIDv7 generator (CPython-based)
- **`src/services/uuid_service.py`**: Photo UUID generation service with Base32 encoding
- **`test/test_uuidv7.py`**: Comprehensive test suite (10 test cases)
- **`test/test_uuid_service.py`**: Service integration tests

### Key Features Delivered

- **48-bit millisecond timestamps** (RFC 9562 compliant)
- **42-bit monotonic counter** for burst mode uniqueness
- **32-bit random tail** for collision resistance
- **Thread-safe implementation** with global state management
- **Counter overflow protection** with timestamp advancement
- **Chronological sorting** (k-sortable) across all generated UUIDs
- **Base32 encoding** for shorter, URL-safe filenames

### Integration Points

**EXIF timestamp → milliseconds conversion** - Handles datetime objects from EXIF data  
**Base32 encoding for filename generation** - 26-character UUID strings  
**Photo metadata incorporation** - Ready for camera info and filename integration  
**Burst mode support** - Monotonic counter handles rapid photo captures

## External References

### Official Specifications

- [RFC 9562 - Universally Unique IDentifiers (UUIDs)](https://www.rfc-editor.org/rfc/rfc9562.html)
- [RFC 9562 Section 5.7 - UUIDv7](https://www.rfc-editor.org/rfc/rfc9562.html#section-5.7)
- [RFC 9562 Section 6.2 - Monotonicity Methods](https://www.rfc-editor.org/rfc/rfc9562.html#section-6.2)

### Python Development

- [CPython Issue #89083 - Support UUIDv6, UUIDv7, and UUIDv8](https://github.com/python/cpython/issues/89083)
- [CPython PR #121119 - UUID7 Implementation](https://github.com/python/cpython/pull/121119)
- [Python Discussions - RFC 9562 Implementation](https://discuss.python.org/t/rfc-4122-9562-uuid-version-7-and-8-implementation/56725)
- [Python 3.14 UUID Documentation](https://docs.python.org/3.14/library/uuid.html)

### Implementation References

- [PostgreSQL UUIDv7 Implementation](https://postgresql.verite.pro/blog/2024/07/15/uuid-v7-pure-sql.html)
- [UUID Format Analysis](https://blog.scaledcode.com/blog/analyzing-new-unique-id/)
- [GitHub UUID6 Draft Discussion](https://github.com/uuid6/uuid6-ietf-draft/issues/24)

## Migration Checklist

When upgrading to Python 3.14+:

- [ ] Remove `src/utils/uuidv7.py`
- [ ] Update imports to use `uuid.uuid7()` from standard library
- [ ] Verify timestamp handling remains millisecond-based
- [ ] Test chronological ordering preservation
- [ ] Update documentation references
- [ ] Remove uuid7/uuid-extension dependencies

