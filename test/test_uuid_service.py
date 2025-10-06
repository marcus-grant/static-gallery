"""Tests for UUID generation service."""

from datetime import datetime

import pytest


class TestUUIDGeneration:
    """Test core UUID generation functionality."""
    
    def test_generate_photo_uuid_basic(self):
        """Test basic UUID generation from photo metadata."""
        from src.services.uuid_service import generate_photo_uuid
        
        timestamp = datetime(2024, 10, 5, 14, 30, 45)
        camera_info = {"make": "Canon", "model": "EOS R5"}
        filename = "IMG_001.jpg"
        
        photo_uuid = generate_photo_uuid(timestamp, camera_info, filename)
        
        # Should be a valid string
        assert isinstance(photo_uuid, str)
        # Should be 26 characters (Base32 encoded UUIDv7)
        assert len(photo_uuid) == 26
        # Should contain only Base32 characters
        assert all(c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567" for c in photo_uuid)