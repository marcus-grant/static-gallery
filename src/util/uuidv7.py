"""RFC 9562 compliant UUIDv7 implementation.

This module provides a standards-compliant UUIDv7 generator based on
the CPython implementation from Python 3.14+.

When Python 3.14+ becomes available, this module should be removed and
replaced with the standard library uuid.uuid7() function.

Based on: https://github.com/python/cpython/pull/121119
License: PSF License Agreement
"""

import secrets
import time
import uuid
from threading import Lock
from typing import Optional


_uuid7_last_timestamp = None
_uuid7_counter = None
_uuid7_lock = Lock()


def uuid7(timestamp_ms: Optional[int] = None) -> uuid.UUID:
    """Generate a UUID version 7 as per RFC 9562.
    
    UUIDv7 features a time-ordered value field derived from the Unix Epoch
    timestamp in milliseconds. Uses 48-bit millisecond timestamp + 42-bit
    counter + 32-bit random tail for monotonicity within same millisecond.
    
    Args:
        timestamp_ms: Optional timestamp in milliseconds since Unix epoch.
                     If None, current time is used.
                     
    Returns:
        A UUID object with version 7.
    """
    global _uuid7_last_timestamp, _uuid7_counter
    
    if timestamp_ms is None:
        timestamp_ms = int(time.time() * 1000)
    
    with _uuid7_lock:
        if _uuid7_last_timestamp is None or timestamp_ms > _uuid7_last_timestamp:
            # New timestamp, reset counter to random value
            _uuid7_counter = secrets.randbits(42)
            _uuid7_last_timestamp = timestamp_ms
        elif timestamp_ms == _uuid7_last_timestamp:
            # Same timestamp, increment counter
            _uuid7_counter = (_uuid7_counter + 1) & ((1 << 42) - 1)
            if _uuid7_counter == 0:
                # Counter overflow, advance timestamp
                timestamp_ms += 1
                _uuid7_last_timestamp = timestamp_ms
        else:
            # Timestamp went backwards, keep existing state
            pass
        
        counter = _uuid7_counter
    
    # Generate 32-bit random tail
    rand_b_tail = secrets.randbits(32)
    
    # Construct UUID integer according to RFC 9562 field layout
    uuid_int = (
        (timestamp_ms & ((1 << 48) - 1)) << 80 |  # 48-bit timestamp
        (7 << 76) |                               # 4-bit version
        ((counter >> 30) & ((1 << 12) - 1)) << 64 |  # 12-bit counter high
        (2 << 62) |                               # 2-bit variant  
        ((counter >> 16) & ((1 << 14) - 1)) << 48 |  # 14-bit counter mid
        ((counter & ((1 << 16) - 1)) << 32) |        # 16-bit counter low
        rand_b_tail                               # 32-bit random
    )
    
    return uuid.UUID(int=uuid_int)