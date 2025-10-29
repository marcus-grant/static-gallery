"""Unit tests for complete GallerySettings dataclass."""
import pytest
from src.models.photo import GallerySettings


class TestGallerySettingsComplete:
    """Unit tests for ensuring GallerySettings includes all required fields."""
    
    def test_gallery_settings_has_all_required_fields(self):
        """Test that GallerySettings dataclass has all processing settings fields."""
        # This test will fail initially - target_timezone_offset_hours missing
        settings = GallerySettings(
            timestamp_offset_hours=0,
            target_timezone_offset_hours=2,  # This field doesn't exist yet
            web_size=(2048, 2048),          # This field doesn't exist yet
            thumb_size=(400, 400),          # This field doesn't exist yet
            jpeg_quality=85,                # This field doesn't exist yet
            webp_quality=85                 # This field doesn't exist yet
        )
        
        assert settings.timestamp_offset_hours == 0
        assert settings.target_timezone_offset_hours == 2
        assert settings.web_size == (2048, 2048)
        assert settings.thumb_size == (400, 400)
        assert settings.jpeg_quality == 85
        assert settings.webp_quality == 85
    
    def test_gallery_settings_defaults(self):
        """Test that GallerySettings has sensible defaults."""
        # Should be able to create with minimal params and get defaults
        settings = GallerySettings()
        
        assert settings.timestamp_offset_hours == 0
        assert settings.target_timezone_offset_hours == 13  # preserve original
        assert settings.web_size == (2048, 2048)
        assert settings.thumb_size == (400, 400)
        assert settings.jpeg_quality == 85
        assert settings.webp_quality == 85
    
    def test_gallery_settings_from_settings_module(self):
        """Test creating GallerySettings from settings module values."""
        import settings
        
        # This test will guide the implementation - should be able to populate
        # GallerySettings from current settings module values
        gallery_settings = GallerySettings(
            timestamp_offset_hours=getattr(settings, 'TIMESTAMP_OFFSET_HOURS', 0),
            target_timezone_offset_hours=getattr(settings, 'TARGET_TIMEZONE_OFFSET_HOURS', 13),
            web_size=getattr(settings, 'WEB_SIZE', (2048, 2048)),
            thumb_size=getattr(settings, 'THUMB_SIZE', (400, 400)),
            jpeg_quality=getattr(settings, 'JPEG_QUALITY', 85),
            webp_quality=getattr(settings, 'WEBP_QUALITY', 85)
        )
        
        # Verify it works with current settings
        assert isinstance(gallery_settings.timestamp_offset_hours, int)
        assert isinstance(gallery_settings.target_timezone_offset_hours, int)
        assert isinstance(gallery_settings.web_size, tuple)
        assert isinstance(gallery_settings.thumb_size, tuple)
        assert isinstance(gallery_settings.jpeg_quality, int)
        assert isinstance(gallery_settings.webp_quality, int)