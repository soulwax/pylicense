# File: src/pylicense/license_handler.py
"""Core functionality for adding and updating license headers."""

import datetime
import logging
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Union


@dataclass
class FilePattern:
    """Configuration for file patterns and their comment styles."""

    extensions: List[str]
    comment_start: str
    comment_end: str = ""  # Empty string for single-line comment styles


# Define supported file patterns and their comment styles
PATTERNS = [
    FilePattern([".py", ".sh", ".bash", ".ps1"], "#", ""),
    FilePattern([".js", ".jsx", ".tsx", ".ts", ".c", ".cpp", ".h", ".hpp"], "//", ""),
    FilePattern([".html", ".xml", ".svg", ".ui", ".qrc"], "<!--", "-->"),
    FilePattern([".css", ".scss", ".less"], "/*", "*/"),
    FilePattern([".java", ".kt", ".scala"], "//", ""),
    FilePattern([".rb", ".rake"], "#", ""),
    FilePattern([".rs", ".go"], "//", ""),
    FilePattern([".php"], "//", ""),
]

# Define directories to ignore
IGNORED_DIRS: Set[str] = {
    "__pycache__",
    "node_modules",
    ".git",
    ".hg",
    ".svn",
    "venv",
    ".venv",
    "build",
    "dist",
    ".pytest_cache",
    ".coverage",
    ".idea",
    ".vscode",
}

# Define binary file extensions to skip
BINARY_EXTENSIONS = {
    ".exe",
    ".dll",
    ".so",
    ".dylib",
    ".bin",
    ".dat",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".ico",
    ".mp3",
    ".mp4",
    ".mkv",
    ".qm",
}

# Define license templates
LICENSE_TEMPLATES: Dict[str, str] = {
    "mit": """The MIT License (MIT)

Copyright (c) {year} {author}

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.""",
    "gpl3": """Copyright (C) {year} {author}

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.""",
    "apache2": """Copyright {year} {author}

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.""",
}


def _normalize_path(path: str) -> str:
    """Normalize path separators to forward slashes."""
    return path.replace(os.sep, "/")


def _get_comment_style(file_path: Path) -> Optional[Tuple[str, str]]:
    """Determine the appropriate comment style for a given file."""
    # Check file extension patterns
    for pattern in PATTERNS:
        if any(str(file_path).lower().endswith(ext) for ext in pattern.extensions):
            return (pattern.comment_start, pattern.comment_end)
    return None


def _is_special_xml_file(file_path: Path) -> bool:
    """Check if file is a special XML-based file that needs declaration preservation."""
    xml_extensions = {".ui", ".qrc", ".xml", ".svg", ".html"}
    return file_path.suffix.lower() in xml_extensions


def is_binary(file_path: Path) -> bool:
    """Check if a file is binary."""
    # Quick check based on extension
    if file_path.suffix.lower() in BINARY_EXTENSIONS:
        return True

    try:
        with open(file_path, "rb") as f:
            # Read first 1024 bytes to determine if file is binary
            chunk = f.read(1024)
            return b"\0" in chunk  # Binary files typically contain null bytes
    except OSError:
        return True


def _format_license_text(
    license_template: str,
    author: str,
    year: Optional[int] = None,
    custom_vars: Optional[Dict[str, str]] = None,
) -> str:
    """Format license text with variables."""
    if year is None:
        year = datetime.datetime.now().year

    # Start with basic replacements
    replacements = {
        "year": str(year),
        "author": author,
    }

    # Add custom variables if provided
    if custom_vars:
        replacements.update(custom_vars)

    # Format the license text with all variables
    return license_template.format(**replacements)


def _create_license_header(
    license_template: str,
    author: str,
    year: Optional[int] = None,
    custom_vars: Optional[Dict[str, str]] = None,
    comment_style: Tuple[str, str] = ("#", ""),
) -> List[str]:
    """Create a properly formatted license header with comments."""

    # Format the license text
    license_text = _format_license_text(license_template, author, year, custom_vars)

    # Split into lines
    lines = license_text.strip().split("\n")

    # Unpack comment style
    comment_start, comment_end = comment_style

    # Format each line with comments
    if comment_end:
        # Multi-line comment style (open the comment block)
        header_lines = [f"{comment_start}"]

        # Add each line of the license
        for line in lines:
            header_lines.append(f" {line}" if line.strip() else " ")

        # Close the comment block
        header_lines.append(f"{comment_end}")
    else:
        # Single-line comment style
        header_lines = [
            f"{comment_start} {line}" if line.strip() else comment_start for line in lines
        ]

    return header_lines


def _has_license_header(content: str, comment_start: str) -> bool:
    """Check if file already has a license header."""
    first_lines = content.split("\n", 10)[:10]  # Check first 10 lines
    license_indicators = ["license", "copyright", "mit", "gpl", "apache", "©"]

    for line in first_lines:
        line_lower = line.lower()
        if line_lower.startswith(comment_start.lower()) and any(
            ind in line_lower for ind in license_indicators
        ):
            return True

    return False


def _extract_year_from_header(content: str, comment_start: str) -> Optional[int]:
    """Extract the year from an existing license header."""
    first_lines = content.split("\n", 10)[:10]  # Check first 10 lines

    # Look for a year pattern (typically 4 digits) in license lines
    year_pattern = re.compile(r"(\b\d{4}\b)")

    for line in first_lines:
        if line.startswith(comment_start):
            match = year_pattern.search(line)
            if match:
                try:
                    return int(match.group(1))
                except ValueError:
                    continue

    return None


def _update_license_year_in_content(content: str, comment_start: str, new_year: int) -> str:
    """Update the year in an existing license header."""
    lines = content.split("\n")
    year_pattern = re.compile(r"(\b\d{4}\b)")

    # Try to update the year in the first 10 lines
    for i in range(min(10, len(lines))):
        if lines[i].startswith(comment_start):
            lines[i] = year_pattern.sub(str(new_year), lines[i], count=1)

    return "\n".join(lines)


def _process_file_with_license(
    file_path: Path,
    license_template: str,
    author: str,
    year: Optional[int] = None,
    *,  # Add a keyword-only arguments separator
    custom_vars: Optional[Dict[str, str]] = None,
    force: bool = False,
) -> bool:
    """
    Process a file with license header.

    Args:
        file_path: Path to the file
        license_template: License template text
        author: Author name
        year: Year for license
        custom_vars: Additional custom variables (keyword-only)
        force: Whether to overwrite existing licenses (keyword-only)

    Returns:
        True if file was processed, False otherwise
    """
    # Rest of the function remains the same
    comment_style = _get_comment_style(file_path)
    if not comment_style:
        logging.debug("Skipping unsupported file type: %s", file_path)
        return False

    comment_start, comment_end = comment_style

    try:
        # Try UTF-8 first
        try:
            content = file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            # Fall back to system default encoding if UTF-8 fails
            content = file_path.read_text()

        # Check if file already has a license header
        if _has_license_header(content, comment_start) and not force:
            logging.debug("File already has license header: %s", file_path)
            return False

        # Create the license header
        header_lines = _create_license_header(
            license_template, author, year, custom_vars, (comment_start, comment_end)
        )

        # Process the file based on its type
        lines = content.splitlines()
        new_content = ""

        if not lines:
            # Empty file
            new_content = "\n".join(header_lines) + "\n"
        elif lines[0].startswith("#!"):
            # Shebang line - preserve it
            shebang = lines[0]
            new_content = f"{shebang}\n" + "\n".join(header_lines) + "\n\n" + "\n".join(lines[1:])
        elif _is_special_xml_file(file_path) and any(
            line.strip().startswith(("<?xml", "<!DOCTYPE")) for line in lines[:2]
        ):
            # XML declaration - preserve it
            xml_decl_lines = []
            content_start_idx = 0

            for i, line in enumerate(lines):
                if line.strip().startswith(("<?xml", "<!DOCTYPE")):
                    xml_decl_lines.append(line)
                    content_start_idx = i + 1
                else:
                    break

            new_content = (
                "\n".join(xml_decl_lines)
                + "\n"
                + "\n".join(header_lines)
                + "\n\n"
                + "\n".join(lines[content_start_idx:])
            )
        else:
            # Regular file - completely replace the content if force is true, otherwise add header
            if force:
                # When force is true, we completely replace the content, not just add the header
                new_content = "\n".join(header_lines) + "\n\n" + "\n".join(lines)
            else:
                # When not forcing, just add the header
                new_content = "\n".join(header_lines) + "\n\n" + content

        # Write with the same encoding we read with
        file_path.write_text(new_content, encoding="utf-8")
        logging.info("Added license header to: %s", file_path)
        return True

    except (OSError, UnicodeDecodeError) as e:
        logging.debug("Failed to process %s: %s", file_path, e)
        return False


def apply_license(
    path: Union[str, Path],
    license_template: str = "mit",
    author: str = "Author",
    year: Optional[int] = None,
    *,  # Add a keyword-only arguments separator
    custom_vars: Optional[Dict[str, str]] = None,
    force: bool = False,
) -> int:
    """
    Apply license header to a file or all files in a directory.

    Args:
        path: File or directory path
        license_template: License template name or custom text
        author: Author name for the license
        year: Year for the license (default: current year)
        custom_vars: Additional custom variables for license template (keyword-only)
        force: Force overwrite existing license headers (keyword-only)

    Returns:
        Number of files processed
    """
    # Rest of the function remains the same
    path = Path(path)

    # If a template name is provided, get the actual template
    license_text = LICENSE_TEMPLATES.get(license_template, license_template)

    # Set default year if not provided
    if year is None:
        year = datetime.datetime.now().year

    # Process a single file
    if path.is_file():
        if is_binary(path):
            logging.debug("Skipping binary file: %s", path)
            return 0

        result = _process_file_with_license(
            path,
            license_text,
            author,
            year,
            custom_vars=custom_vars,
            force=force,  # Use keyword arguments
        )
        return 1 if result else 0

    # Process a directory
    if not path.is_dir():
        logging.error("Path does not exist: %s", path)
        return 0

    processed = 0
    for root, dirs, files in os.walk(path):
        # Skip ignored directories
        dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]

        for file in files:
            file_path = Path(root) / file

            if is_binary(file_path):
                logging.debug("Skipping binary file: %s", file_path)
                continue

            result = _process_file_with_license(
                file_path, license_text, author, year, custom_vars=custom_vars, force=force
            )
            if result:
                processed += 1

    return processed


def update_license_year(path: Union[str, Path], new_year: Optional[int] = None) -> int:
    """
    Update the year in existing license headers.

    Args:
        path: File or directory path
        new_year: New year to use (default: current year)

    Returns:
        Number of files updated
    """
    path = Path(path)

    # Set default year if not provided
    if new_year is None:
        new_year = datetime.datetime.now().year

    updated = 0

    # Handle single file
    if path.is_file():
        updated = _update_single_file_year(path, new_year)
        return updated

    # Handle directory
    if not path.is_dir():
        logging.error("Path does not exist: %s", path)
        return 0

    # Process directory
    return _update_directory_years(path, new_year)


# src/pylicense/license_handler.py - Fix _update_single_file_year to reduce returns
def _update_single_file_year(path: Path, new_year: int) -> int:
    """Update the year in a single file's license header."""
    result = 0

    if not is_binary(path):
        comment_style = _get_comment_style(path)
        if comment_style:
            try:
                # Try UTF-8 first
                try:
                    content = path.read_text(encoding="utf-8")
                except UnicodeDecodeError:
                    # Fall back to system default encoding if UTF-8 fails
                    content = path.read_text()

                # Check if file has a license header with year
                if _has_license_header(content, comment_style[0]):
                    # Extract current year
                    current_year = _extract_year_from_header(content, comment_style[0])
                    if current_year is not None and current_year != new_year:
                        updated_content = _update_license_year_in_content(
                            content, comment_style[0], new_year
                        )
                        path.write_text(updated_content, encoding="utf-8")
                        logging.info("Updated license year in: %s", path)
                        result = 1
            except (OSError, UnicodeDecodeError) as e:
                logging.debug("Failed to process %s: %s", path, e)

    return result


def _update_directory_years(directory: Path, new_year: int) -> int:
    """Update license years in all files in a directory."""
    updated = 0

    for root, dirs, files in os.walk(directory):
        # Skip ignored directories
        dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]

        for file in files:
            file_path = Path(root) / file
            updated += _update_single_file_year(file_path, new_year)

    return updated


def verify_license(
    path: Union[str, Path],
    license_template: str = "mit",
) -> Tuple[int, int]:
    """Verify that files have the correct license header."""
    path = Path(path)

    # Get license key phrases directly from template name
    license_key_phrases = _get_license_key_phrases(license_template)

    # Process either a single file or directory
    if path.is_file():
        if is_binary(path) or not _get_comment_style(path):
            return (0, 0)
        result = _check_file_license(path, license_key_phrases)
        return (1 if result else 0, 1)

    # Process a directory
    if not path.is_dir():
        logging.error("Path does not exist: %s", path)
        return (0, 0)

    return _verify_directory_licenses(path, license_key_phrases)


def _get_license_key_phrases(license_template: str) -> List[str]:
    """Get key phrases to identify a specific license type."""
    if license_template == "mit":
        return [
            "mit license",
            "permission is hereby granted",
            "without restriction",
            "the software is provided as is",
        ]
    if license_template == "gpl3":
        return [
            "free software",
            "gnu general public license",
            "without warranty",
            "see the gnu general public license",
        ]
    if license_template == "apache2":
        return [
            "apache license",
            "licensed under the apache license",
            "without warranties or conditions",
            "licenses this file",
        ]
    return ["copyright", "license"]  # Generic fallback


def _check_file_license(file_path: Path, license_key_phrases: List[str]) -> bool:
    """Check if a file has the expected license."""
    if is_binary(file_path):
        return False

    comment_style = _get_comment_style(file_path)
    if not comment_style:
        return False

    try:
        # Try UTF-8 first
        try:
            content = file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            # Fall back to system default encoding if UTF-8 fails
            content = file_path.read_text()

        # Check if file has any license header
        if not _has_license_header(content, comment_style[0]):
            return False

        # Get the first 20 lines to check for license
        first_lines = content.split("\n", 20)[:20]
        content_to_check = "\n".join(first_lines)

        # Normalize content for comparison
        norm_content = re.sub(r"\s+", " ", content_to_check.lower())

        # Check for key phrases that identify the specific license
        # This approach is more reliable than exact matching
        phrase_matches = 0
        for phrase in license_key_phrases:
            if phrase in norm_content:
                phrase_matches += 1

        # If we match most of the key phrases, consider it a match
        # This handles slight variations in formatting
        return phrase_matches >= len(license_key_phrases) / 2

    except (OSError, UnicodeDecodeError):
        return False


def _verify_directory_licenses(directory: Path, license_key_phrases: List[str]) -> Tuple[int, int]:
    """Verify licenses in all files in a directory."""
    files_with_license = 0
    total_files = 0

    for root, dirs, files in os.walk(directory):
        # Skip ignored directories
        dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]

        for file in files:
            file_path = Path(root) / file

            if is_binary(file_path):
                continue

            if not _get_comment_style(file_path):
                continue

            total_files += 1
            if _check_file_license(file_path, license_key_phrases):
                files_with_license += 1

    return (files_with_license, total_files)


def create_license_file(
    path: Union[str, Path],
    license_template: str = "mit",
    author: str = "Author",
    year: Optional[int] = None,
    custom_vars: Optional[Dict[str, str]] = None,
) -> bool:
    """
    Create a LICENSE file in the specified directory.

    Args:
        path: Directory path where to create the license file
        license_template: License template name or custom text
        author: Author name for the license
        year: Year for the license (default: current year)
        custom_vars: Additional custom variables for license template

    Returns:
        True if license file was created, False otherwise
    """
    path = Path(path)

    # Ensure path is a directory
    if not path.is_dir():
        logging.error("Path is not a directory: %s", path)
        return False

    # If a template name is provided, get the actual template
    license_text = LICENSE_TEMPLATES.get(license_template, license_template)

    # Format the license text
    formatted_license = _format_license_text(license_text, author, year, custom_vars)

    # Write the license file
    license_file = path / "LICENSE"
    try:
        license_file.write_text(formatted_license, encoding="utf-8")
        logging.info("Created LICENSE file at: %s", license_file)
        return True
    except OSError as e:
        logging.error("Failed to create LICENSE file: %s", e)
        return False


# Add support for configuration
class LicenseConfig:
    """Configuration manager for the license tool."""

    def __init__(self):
        """Initialize configuration with defaults."""
        self.license_templates = LICENSE_TEMPLATES.copy()
        self.patterns = PATTERNS.copy()
        self.ignored_dirs = IGNORED_DIRS.copy()

    def add_license_template(self, name: str, template: str) -> None:
        """
        Add a custom license template.

        Args:
            name: Template name
            template: License text with {year} and {author} placeholders
        """
        self.license_templates[name] = template

    def add_file_pattern(
        self, extensions: List[str], comment_start: str, comment_end: str = ""
    ) -> None:
        """
        Add a custom file pattern.

        Args:
            extensions: List of file extensions (with dot)
            comment_start: Comment start marker
            comment_end: Comment end marker (optional)
        """
        self.patterns.append(FilePattern(extensions, comment_start, comment_end))

    def add_ignored_dir(self, dir_name: str) -> None:
        """
        Add a directory to ignore.

        Args:
            dir_name: Directory name to ignore
        """
        self.ignored_dirs.add(dir_name)

    def remove_ignored_dir(self, dir_name: str) -> bool:
        """
        Remove a directory from the ignore list.

        Args:
            dir_name: Directory name to remove

        Returns:
            True if directory was removed, False if not in the list
        """
        if dir_name in self.ignored_dirs:
            self.ignored_dirs.remove(dir_name)
            return True
        return False


# Create a global config instance
config = LicenseConfig()
