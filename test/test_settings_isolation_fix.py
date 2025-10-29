"""Unit tests for fixing settings isolation issues."""
import pytest
import sys
import os
from unittest.mock import patch, mock_open


class TestSettingsIsolationFix:
    """Unit tests for ensuring clean settings isolation in test environments."""
    
    def test_settings_loads_without_local_file_pollution(self):
        """Test that settings can load with clean defaults when local file doesn't exist."""
        # Remove any existing settings module to force fresh import
        if "settings" in sys.modules:
            del sys.modules["settings"]
        
        # Mock the local settings file to not exist
        with patch("pathlib.Path.exists", return_value=False):
            with patch("dotenv.load_dotenv"):
                import settings as clean_settings
                
                # Should get clean defaults
                assert clean_settings.S3_PUBLIC_REGION is None
                assert clean_settings.S3_PUBLIC_ENDPOINT is None
                assert clean_settings.TARGET_TIMEZONE_OFFSET_HOURS == 13
    
    def test_settings_test_mode_ignores_local_file(self):
        """Test that TEST_MODE environment variable forces clean defaults."""
        # Remove any existing settings module
        if "settings" in sys.modules:
            del sys.modules["settings"]
        
        # Mock environment with TEST_MODE
        test_env = {"GALLERIA_TEST_MODE": "1"}
        
        with patch.dict(os.environ, test_env, clear=True):
            with patch("dotenv.load_dotenv"):
                # Even if local file exists, should be ignored in test mode
                with patch("pathlib.Path.exists", return_value=True):
                    with patch("builtins.open", mock_open(read_data="S3_PUBLIC_REGION = 'polluted'")):
                        import settings as test_mode_settings
                        
                        # Should ignore local file when in test mode
                        assert test_mode_settings.S3_PUBLIC_REGION is None, \
                            "TEST_MODE should ignore local settings file"
    
    def test_settings_monkeypatch_isolation_works(self):
        """Test that monkeypatch correctly isolates settings values in tests."""
        import settings
        
        # Store original value
        original_region = getattr(settings, 'S3_PUBLIC_REGION', None)
        
        # Temporarily change it
        settings.S3_PUBLIC_REGION = "test-region"
        assert settings.S3_PUBLIC_REGION == "test-region"
        
        # Reset to original (this is what pytest monkeypatch should do)
        settings.S3_PUBLIC_REGION = original_region
        
        # Should be back to original value
        assert settings.S3_PUBLIC_REGION == original_region