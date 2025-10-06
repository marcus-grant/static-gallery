"""Tests for RFC 9562 compliant UUIDv7 implementation."""

import time
import uuid
import struct
from datetime import datetime, timezone

import pytest

from src.util.uuidv7 import uuid7


class TestUUIDv7RFC9562Compliance:
    """Test RFC 9562 compliance for UUIDv7 implementation."""
    
    def test_uuid7_basic_generation(self):
        """Test basic UUID7 generation returns valid UUID."""
        result = uuid7()
        
        assert isinstance(result, uuid.UUID)
        assert result.version == 7
        assert result.variant == uuid.RFC_4122
    
    def test_uuid7_field_layout(self):
        """Test UUID7 follows RFC 9562 field layout."""
        # Generate with known timestamp
        timestamp_ms = 1609459200000  # 2021-01-01 00:00:00 UTC
        result = uuid7(timestamp_ms)
        
        # Extract fields from UUID bytes
        uuid_bytes = result.bytes
        
        # First 48 bits should contain the timestamp
        timestamp_from_uuid = struct.unpack('>Q', b'\x00\x00' + uuid_bytes[:6])[0]
        assert timestamp_from_uuid == timestamp_ms
        
        # Version bits (4 bits at position 48-51) should be 0111 (7)
        version_byte = uuid_bytes[6]
        version = (version_byte >> 4) & 0xF
        assert version == 7
        
        # Variant bits (2 bits at position 64-65) should be 10
        variant_byte = uuid_bytes[8]
        variant = (variant_byte >> 6) & 0x3
        assert variant == 2  # Binary 10
    
    def test_uuid7_millisecond_precision(self):
        """Test UUID7 uses millisecond precision, not nanoseconds."""
        # Test with specific millisecond timestamp
        dt = datetime(2024, 1, 1, 12, 0, 0, 500000, tzinfo=timezone.utc)
        timestamp_ms = int(dt.timestamp() * 1000)
        
        result = uuid7(timestamp_ms)
        
        # Extract timestamp from UUID
        uuid_bytes = result.bytes
        extracted_ms = struct.unpack('>Q', b'\x00\x00' + uuid_bytes[:6])[0]
        
        assert extracted_ms == timestamp_ms


class TestUUIDv7BurstMode:
    """Test burst mode handling for same millisecond generation."""
    
    def test_burst_mode_same_millisecond(self):
        """Test multiple UUIDs generated in same millisecond are unique."""
        # Generate multiple UUIDs with same timestamp
        timestamp_ms = int(time.time() * 1000)
        uuids = [uuid7(timestamp_ms) for _ in range(100)]
        
        # All should be unique
        assert len(set(uuids)) == 100
        
        # All should have same timestamp portion
        for u in uuids:
            ts = struct.unpack('>Q', b'\x00\x00' + u.bytes[:6])[0]
            assert ts == timestamp_ms
    
    def test_burst_mode_maintains_ordering(self):
        """Test burst mode maintains chronological ordering."""
        timestamp_ms = int(time.time() * 1000)
        uuids = [uuid7(timestamp_ms) for _ in range(50)]
        
        # When sorted, should maintain generation order for same timestamp
        # This tests the monotonic counter behavior
        for i in range(len(uuids) - 1):
            assert uuids[i] < uuids[i + 1]
    
    def test_counter_overflow_handling(self):
        """Test handling of counter overflow within same millisecond."""
        # This tests the implementation's overflow protection
        timestamp_ms = int(time.time() * 1000)
        
        # Generate many UUIDs with same timestamp
        uuids = []
        for _ in range(1000):
            u = uuid7(timestamp_ms)
            uuids.append(u)
        
        # All should be unique
        assert len(set(uuids)) == 1000
        
        # All should maintain chronological order
        for i in range(len(uuids) - 1):
            assert uuids[i] < uuids[i + 1]


class TestUUIDv7ThreadSafety:
    """Test thread safety of UUID7 generation."""
    
    def test_concurrent_generation(self):
        """Test UUID7 generation is thread-safe."""
        from concurrent.futures import ThreadPoolExecutor
        import threading
        
        uuids = []
        lock = threading.Lock()
        
        def generate_uuids(count):
            local_uuids = []
            for _ in range(count):
                u = uuid7()
                local_uuids.append(u)
            with lock:
                uuids.extend(local_uuids)
        
        # Generate UUIDs from multiple threads
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(generate_uuids, 100) for _ in range(10)]
            for future in futures:
                future.result()
        
        # All UUIDs should be unique
        assert len(set(uuids)) == 1000
    
    def test_concurrent_same_timestamp(self):
        """Test thread-safe generation with same timestamp."""
        from concurrent.futures import ThreadPoolExecutor
        import threading
        
        uuids = []
        lock = threading.Lock()
        timestamp_ms = int(time.time() * 1000)
        
        def generate_uuids(count):
            local_uuids = []
            for _ in range(count):
                u = uuid7(timestamp_ms)
                local_uuids.append(u)
            with lock:
                uuids.extend(local_uuids)
        
        # Generate UUIDs from multiple threads with same timestamp
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(generate_uuids, 50) for _ in range(5)]
            for future in futures:
                future.result()
        
        # All UUIDs should be unique despite same timestamp
        assert len(set(uuids)) == 250


class TestUUIDv7ChronologicalOrdering:
    """Test chronological ordering (k-sortable) functionality."""
    
    def test_chronological_sorting(self):
        """Test UUIDs sort chronologically across different timestamps."""
        uuids = []
        timestamps = []
        
        # Generate UUIDs with increasing timestamps
        for i in range(10):
            timestamp_ms = int(time.time() * 1000) + i * 10
            timestamps.append(timestamp_ms)
            uuids.append(uuid7(timestamp_ms))
        
        # Sort UUIDs lexicographically
        sorted_uuids = sorted(uuids)
        
        # Should be in same order as generation
        assert sorted_uuids == uuids
        
        # Verify timestamps are in order
        for i in range(len(sorted_uuids) - 1):
            bytes1 = sorted_uuids[i].bytes
            bytes2 = sorted_uuids[i + 1].bytes
            ts1 = struct.unpack('>Q', b'\x00\x00' + bytes1[:6])[0]
            ts2 = struct.unpack('>Q', b'\x00\x00' + bytes2[:6])[0]
            assert ts1 <= ts2
    
    def test_mixed_timestamp_ordering(self):
        """Test ordering with mixed timestamps including same millisecond."""
        # Generate UUIDs with some overlapping timestamps
        uuids = []
        base_time = int(time.time() * 1000)
        
        # Mix of different and same timestamps
        timestamps = [base_time, base_time + 1, base_time, base_time + 2, base_time + 1]
        
        for ts in timestamps:
            uuids.append(uuid7(ts))
        
        # Sort and verify chronological order
        sorted_uuids = sorted(uuids)
        
        for i in range(len(sorted_uuids) - 1):
            bytes1 = sorted_uuids[i].bytes
            bytes2 = sorted_uuids[i + 1].bytes
            ts1 = struct.unpack('>Q', b'\x00\x00' + bytes1[:6])[0]
            ts2 = struct.unpack('>Q', b'\x00\x00' + bytes2[:6])[0]
            
            # Timestamps should be in non-decreasing order
            assert ts1 <= ts2