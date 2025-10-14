# Development Guidelines

## Testing Requirements

- **Test Command**: Use `uv run pytest` to run tests (NOT `python -m pytest`)
- **Specific Test Files**: Use `uv run pytest test/test_filename.py -v` for focused testing
- ALWAYS run tests before suggesting a commit
- Follow E2E + TDD approach:
  - E2E tests find larger missing or broken pieces
  - TDD fills or fixes those pieces incrementally
- TDD/E2E workflow:
  - Build tests singularly first
  - Ensure test fails as expected (red)
  - Implement change to make test pass (green)
  - Consider refactors for better solution (refactor)
  - Move to next test when complete
- Task management:
  - Each test typically corresponds to a TODO task
  - Some tasks require multiple tests
  - After test(s) pass and refactors complete: update TODO.md, git commit
- Implement in small steps with clear logical breaks:
  - Add one test case or feature at a time
  - Test immediately after each testable addition
  - Never write massive amounts of code without testing
- Template tests with BeautifulSoup4 to verify HTML structure

## Commit Message Format

- Title: Maximum 50 characters including prefix
- Body: Maximum 72 characters per line
- Body text should use '-' bullets with proper nesting
- Use prefixes:
  - `Tst:` for test-related changes
  - `Fix:` for bug fixes
  - `Ft:` for new features
  - `Ref:` for refactoring
  - `Doc:` for documentation
  - `Pln:` for planning/TODO updates
- No signature block - do not include emoji, links, or Co-Authored-By lines

## Code Style

- Follow existing patterns in the codebase
- Check neighboring files for conventions
- Never assume a library is available - verify in package.json/requirements
- Don't add comments unless explicitly asked
- Match indentation and formatting of existing code
- Follow PEP 8, ruff and typical Python conventions:
  - No trailing whitespace
  - Blank line at end of file
  - Two blank lines between top-level definitions
  - One blank line between method definitions
  - Spaces around operators and after commas
  - No unnecessary blank lines within functions
  - Maximum line length of 88 characters (Black/Ruff default)
- **2-space indentation** throughout templates and JS (NOT Python - Python uses 4 spaces)

## Key Implementation Details

- **Static-first MVP**: Render all photos server-side, add interactivity with minimal JS
- **Photo Modal Features**: 
  - 80% viewport sizing (keeping 20% for dismiss area)
  - Left/right navigation zones (25% each side)
  - Wrap-around navigation (first ↔ last)
  - ESC key and backdrop click to close
- **Post-Deploy Features**: Checkbox selection, progressive loading, BunnyCDN analytics

## Project-Specific Instructions

- This is a custom static site generator based gallery named "Galleria"
- Supports preprocessing copies of a specific wedding photo collection
- Current focus areas are tracked in TODO.md
- Keep TODO.md updated:
  - Update "Current Tasks" section when starting/stopping work
  - Mark completed items with [x]
  - Add new tasks as they're discovered
  - Document progress for easy resumption
- Keep `./doc` updated
  - `doc/README.md`
    - The overview and index to other documentation documents
  - The rest are named after key documentation areas

## Important Reminders

- Do what has been asked; nothing more, nothing less
- NEVER create files unless they're absolutely necessary for achieving your goal
- ALWAYS prefer editing an existing file to creating a new one
- NEVER proactively create documentation files (*.md) or README files unless explicitly requested