"""Integration test for settings isolation in different environments."""
import pytest
import sys
import os
from pathlib import Path
from unittest.mock import patch
from pyfakefs.fake_filesystem_unittest import Patcher


class TestSettingsEnvironmentIsolation:
    """Integration tests for settings isolation between test and production environments."""
    
    def test_settings_defaults_in_clean_environment(self):
        """Test that settings load with proper defaults in clean test environment."""
        # Remove any existing settings module to force fresh import
        if "settings" in sys.modules:
            del sys.modules["settings"]
        
        # Mock environment to avoid local settings file pollution
        with patch.dict(os.environ, {"GALLERIA_TEST_MODE": "1"}, clear=True):
            with patch("dotenv.load_dotenv"):
                # This should import clean defaults without local settings pollution
                import settings as test_settings
                
                # Critical test: S3 settings should be None by default
                assert test_settings.S3_PUBLIC_REGION is None, \
                    f"S3_PUBLIC_REGION should be None but got '{test_settings.S3_PUBLIC_REGION}' - " \
                    "settings.local.py is polluting test environment"
                
                assert test_settings.S3_PUBLIC_ENDPOINT is None
                assert test_settings.S3_PUBLIC_ACCESS_KEY is None
                assert test_settings.S3_PUBLIC_SECRET_KEY is None
                assert test_settings.S3_PUBLIC_BUCKET is None
                
                # Timezone settings should have defaults
                assert test_settings.TIMESTAMP_OFFSET_HOURS == 0
                assert test_settings.TARGET_TIMEZONE_OFFSET_HOURS == 13  # preserve original
    
    def test_settings_local_file_isolation(self):
        """Test that local settings file doesn't affect test environment."""
        # Use pyfakefs to create a controlled filesystem environment
        with Patcher() as patcher:
            fs = patcher.fs
            
            # Remove existing settings module
            if "settings" in sys.modules:
                del sys.modules["settings"]
            
            # Create a clean settings.py file (simulate production default)
            settings_content = '''
from pathlib import Path
import os
from dotenv import load_dotenv

# Base configuration
BASE_DIR = Path(__file__).resolve().parent

# S3 Settings - should default to None
S3_PUBLIC_ENDPOINT = None
S3_PUBLIC_ACCESS_KEY = None  
S3_PUBLIC_SECRET_KEY = None
S3_PUBLIC_BUCKET = None
S3_PUBLIC_REGION = None

# Timezone settings
TIMESTAMP_OFFSET_HOURS = 0
TARGET_TIMEZONE_OFFSET_HOURS = 13

# Load environment variables if .env exists
load_dotenv()

# Try to load local settings but fail gracefully
try:
    from settings.local import *
except ImportError:
    pass
'''
            
            fs.create_file("settings.py", contents=settings_content)
            
            # Create a settings.local.py that would pollute defaults
            local_settings_content = '''
S3_PUBLIC_REGION = "eu-central-1"
S3_PUBLIC_ENDPOINT = "https://polluted.endpoint.com"
TARGET_TIMEZONE_OFFSET_HOURS = 2
'''
            fs.create_file("settings/local.py", contents=local_settings_content)
            
            # Mock dotenv and environment to prevent pollution
            with patch.dict(os.environ, {}, clear=True):
                with patch("dotenv.load_dotenv"):
                    # Import should get clean defaults, not polluted values
                    import settings as clean_settings
                    
                    # This test will fail because settings isolation isn't working properly
                    assert clean_settings.S3_PUBLIC_REGION is None, \
                        "Settings isolation failed - local settings are bleeding into test environment"
    
    def test_environment_variable_override_works(self):
        """Test that environment variables properly override settings."""
        # Remove existing settings module
        if "settings" in sys.modules:
            del sys.modules["settings"]
        
        # Set specific environment variables
        test_env = {
            "GALLERIA_S3_PUBLIC_REGION": "us-west-2",
            "GALLERIA_TARGET_TIMEZONE_OFFSET_HOURS": "5",
            "GALLERIA_TIMESTAMP_OFFSET_HOURS": "-4"
        }
        
        with patch.dict(os.environ, test_env, clear=True):
            with patch("dotenv.load_dotenv"):
                import settings as env_settings
                
                # Environment variables should override defaults
                assert env_settings.S3_PUBLIC_REGION == "us-west-2"
                assert env_settings.TARGET_TIMEZONE_OFFSET_HOURS == 5
                assert env_settings.TIMESTAMP_OFFSET_HOURS == -4
    
    def test_production_settings_vs_test_settings_isolation(self):
        """Test that production settings don't leak into test environment."""
        # Simulate production environment with local settings
        production_settings = {
            "S3_PUBLIC_REGION": "eu-central-1",
            "S3_PUBLIC_ENDPOINT": "https://production.bucket.com",
            "TARGET_TIMEZONE_OFFSET_HOURS": 2,
            "TIMESTAMP_OFFSET_HOURS": 0
        }
        
        # Test environment should be isolated from production
        with Patcher() as patcher:
            fs = patcher.fs
            
            # Remove existing settings module
            if "settings" in sys.modules:
                del sys.modules["settings"]
            
            # Create production-like local settings
            local_settings = "\n".join([
                f"{key} = {repr(value)}"
                for key, value in production_settings.items()
            ])
            
            fs.create_file("settings.local.py", contents=local_settings)
            
            # In test environment, these production settings should be ignored
            with patch.dict(os.environ, {"GALLERIA_TEST_MODE": "1"}, clear=True):
                with patch("dotenv.load_dotenv"):
                    # This test will initially fail - shows settings isolation problem
                    import settings as test_isolated_settings
                    
                    # In test mode, should get defaults, not production values
                    assert test_isolated_settings.S3_PUBLIC_REGION is None, \
                        "Production settings leaked into test environment"
                    
                    assert test_isolated_settings.TARGET_TIMEZONE_OFFSET_HOURS == 13, \
                        "Production timezone settings leaked into test environment"