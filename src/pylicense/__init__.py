# File: src/pylicense/__init__.py
"""
PyLicense - A tool for managing license headers and files in projects.

This package provides functionality to automatically add, update, or verify
license headers in various programming language files.
"""

from .license_handler import (
    IGNORED_DIRS,
    LICENSE_TEMPLATES,
    PATTERNS,
    FilePattern,
    apply_license,
    update_license_year,
    verify_license,
)

__version__ = "0.1.0"

__all__ = [
    "apply_license",
    "update_license_year",
    "verify_license",
    "FilePattern",
    "PATTERNS",
    "IGNORED_DIRS",
    "LICENSE_TEMPLATES",
]
