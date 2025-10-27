# Testing Documentation

This directory contains documentation for the Galleria testing infrastructure and patterns.

## Testing Files

- [fixtures.md](fixtures.md) - Test fixtures and isolation patterns
- [patterns.md](patterns.md) - Testing patterns and best practices (planned)

## Testing Overview

Galleria uses pytest with a comprehensive test suite focused on:
- **Unit tests** for individual services and functions
- **Integration tests** for photo processing workflows  
- **Synthetic photo generation** for reproducible, CI-friendly testing
- **Proper test isolation** to prevent local configuration interference

## Key Testing Commands

```bash
# Run all tests
uv run pytest

# Run specific test file with verbose output
uv run pytest test/test_filename.py -v

# Run specific test class or method
uv run pytest test/test_exif.py::TestGetDatetimeTaken -v
```

## Test Structure

```
test/
├── test_*.py           # Unit tests for main modules
├── services/           # Service layer tests
│   └── test_*.py
├── command/            # Command layer tests  
│   └── test_*.py
└── integration/        # Integration tests
    └── test_*.py
```

See [doc/CONTRIBUTE.md](../CONTRIBUTE.md) for development workflow and testing requirements.