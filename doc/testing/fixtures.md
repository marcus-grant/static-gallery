# Test Fixtures and Isolation

## Critical Testing Patterns

### Settings Isolation with `autouse` Fixtures

**Problem**: Local settings files (like `settings.local.py`) can interfere with tests, causing different behavior in different environments.

**Solution**: Use `autouse=True` fixtures to ensure consistent test behavior regardless of local configuration.

#### Pattern Implementation

```python
import pytest
import settings

@pytest.fixture(autouse=True)
def reset_timestamp_offset(monkeypatch):
    """Reset TIMESTAMP_OFFSET_HOURS to 0 for all tests unless explicitly overridden"""
    monkeypatch.setattr(settings, 'TIMESTAMP_OFFSET_HOURS', 0)
```

#### Current Usage

This pattern is implemented in:
- `test/test_exif.py` - Ensures EXIF tests have consistent offset behavior
- `test/test_settings.py` - Prevents local settings from affecting settings tests  
- `test/services/test_file_processing_dual.py` - Ensures photo processing tests are isolated

#### When to Use

Use `autouse` fixtures when:
- Settings can be modified by local configuration files
- Tests need to run consistently across different environments
- CI/CD requires reproducible test behavior
- Multiple tests in a file need the same baseline configuration

#### Explicit Override Pattern

When specific tests need different settings:

```python
def test_with_specific_offset(self, monkeypatch):
    """Test behavior with specific offset value"""
    # Override the autouse fixture for this specific test
    monkeypatch.setattr(settings, 'TIMESTAMP_OFFSET_HOURS', -4)
    
    # Test logic here...
```

## Synthetic Photo Generation

### `create_photo_with_exif` Fixture

Creates test images with custom EXIF data using PIL and piexif:

```python
def test_example(self, create_photo_with_exif):
    """Example test using synthetic photo generation"""
    photo_path = create_photo_with_exif(
        "test_photo.jpg",
        DateTimeOriginal="2023:09:15 14:30:45",
        Make="Canon",
        Model="EOS R5"
    )
    
    # Test with the synthetic photo...
```

**Benefits**:
- **CI/CD Compatible**: No dependency on real photo files
- **Reproducible**: Same synthetic photos every test run
- **Fast**: Small test images generate quickly
- **Flexible**: Custom EXIF data for specific test scenarios

### Available EXIF Tags

The fixture supports common EXIF tags:
- `DateTimeOriginal` - Photo timestamp
- `SubSecTimeOriginal` - Subsecond precision  
- `Make` / `Model` - Camera information
- `OffsetTimeOriginal` / `OffsetTimeDigitized` - Timezone offsets

## Best Practices

1. **Always use synthetic photos** for automated testing (not real photo files)
2. **Use `autouse` fixtures** for consistent settings across test files
3. **Explicit overrides** when testing specific configuration scenarios
4. **Test isolation** - each test should be independent of others
5. **Clear test names** that describe the scenario being tested

## Testing the EXIF Offset System

The EXIF timestamp offset system uses these patterns:

```python
class TestGetDatetimeTakenWithOffset:
    def test_applies_timestamp_offset_when_configured(self, create_photo_with_exif, monkeypatch):
        """Test that offset is applied correctly"""
        # Override autouse fixture for this specific test
        monkeypatch.setattr(settings, 'TIMESTAMP_OFFSET_HOURS', -4)
        
        # Create synthetic photo with known timestamp
        photo_path = create_photo_with_exif(DateTimeOriginal="2023:09:15 14:30:45")
        
        # Verify offset is applied: 14:30:45 - 4 hours = 10:30:45
        result = exif.get_datetime_taken(photo_path)
        expected = datetime(2023, 9, 15, 10, 30, 45)
        assert result == expected
```

This ensures:
- Tests are reproducible across environments
- Local configuration doesn't interfere with test results
- Both default behavior (no offset) and offset behavior are tested
- CI/CD systems get consistent results