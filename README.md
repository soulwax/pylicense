# PyLicense Project

PyLicense is a Python tool for managing license headers and files in projects. It allows you to easily add, update, and verify license headers across your codebase.

## Project Structure

```plaintext
├───.gitignore
├───LICENSE
├───Makefile
├───MANIFEST.in
├───pyproject.toml
├───README.md
├───requirements-dev.txt
├───requirements.txt
├───setup.py
├───.github
│   └───workflows
│       └───python-package.yml
├───src
│   └───pylicense
│       ├───__init__.py
│       ├───license_handler.py
│       └───cli.py
└───tests
    ├───__init__.py
    ├───test_license_handler.py
    └───test_cli.py
```

## Key Features

- Automatically adds and updates license headers in various file types
- Supports multiple license types (MIT, GPL3, Apache2)
- Preserves important file elements like shebangs and XML declarations
- Detects and skips binary files
- Command-line interface for easy usage
- Can create standalone LICENSE files
- Verification mode to check license compliance
- Year updating to keep licenses current

## Usage

### Command-Line Interface

```bash
# Add MIT license headers to all files in the current directory
pylicense

# Use a specific license template
pylicense --template gpl3

# Specify the author name
pylicense --author "Your Name"

# Specify a custom year
pylicense --year 2025

# Work with a specific directory
pylicense -d /path/to/project

# Update the year in existing license headers
pylicense --update-year

# Verify license headers
pylicense --verify

# Create a LICENSE file
pylicense --create-license-file

# Force overwrite existing licenses
pylicense --force

# Enable verbose logging
pylicense -v
```

### Python API

```python
from pathlib import Path
from pylicense import apply_license, update_license_year, verify_license

# Add license headers to files
apply_license(
    path=Path("your_project"),
    license_template="mit",
    author="Your Name",
    year=2025,
    force=False
)

# Update license years
update_license_year(Path("your_project"), new_year=2025)

# Verify license headers
files_with_license, total_files = verify_license(
    Path("your_project"),
    license_template="mit"
)
print(f"License compliance: {files_with_license}/{total_files} files")

# Custom configuration
from pylicense.license_handler import config

# Add custom license template
config.add_license_template(
    "custom",
    "Copyright (c) {year} {author}\nAll rights reserved."
)

# Add custom file patterns
config.add_file_pattern([".custom"], "//")

# Add directories to ignore
config.add_ignored_dir("vendor")
```

## Supported File Types

PyLicense automatically recognizes and applies the appropriate comment styles:

- Python (.py), Shell scripts (.sh, .bash, .ps1): `#`
- JavaScript/TypeScript (.js, .jsx, .ts, .tsx), C/C++ (.c, .cpp, .h, .hpp): `//`
- HTML/XML (.html, .xml, .svg): `<!-- -->`
- CSS/SCSS (.css, .scss, .less): `/* */`
- And many more file types

## Installation

```bash
# From PyPI (once available)
pip install pylicense

# From source
git clone https://github.com/your_username/pylicense.git
cd pylicense
pip install -e .
```

## Development

```bash
# Clone the repository
git clone https://github.com/your_username/pylicense.git
cd pylicense

# Install dependencies
pip install -r requirements-dev.txt

# Run tests
pytest

# Check test coverage
pytest --cov=pylicense tests/

# Format code
black src/pylicense tests
isort src/pylicense tests

# Lint code
pylint src/pylicense tests
```

## License

This project is licensed under the GNU General Public License v3.0.
