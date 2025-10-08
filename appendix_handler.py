"""
Appendix handler with dependency resolution.
"""

import os
import re
from typing import Dict, Set, List, Optional
from pathlib import Path
from logger_config import setup_logger

logger = setup_logger(__name__)


class AppendixHandler:
    """Handles appendix files with dependency resolution."""

    def __init__(self, appendix_dir: str = "appendixes"):
        self.appendix_dir = Path(appendix_dir)
        self.dependencies: Dict[str, Set[str]] = {}
        self.appendix_metadata: Dict[str, Dict] = {}

    def scan_appendixes(self):
        """Scan all appendix files and parse their dependencies."""
        if not self.appendix_dir.exists():
            return

        for tex_file in self.appendix_dir.glob("*.tex"):
            filename = tex_file.name
            deps = self._parse_dependencies(tex_file)
            self.dependencies[filename] = deps

            # Extract metadata like title
            self.appendix_metadata[filename] = self._extract_metadata(tex_file)

    def _parse_dependencies(self, file_path: Path) -> Set[str]:
        """Parse DEPENDS_ON comments from a file."""
        deps = set()
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    # Look for % DEPENDS_ON: filename.tex or multiple files
                    match = re.match(r'%\s*DEPENDS_ON:\s*(.+)', line.strip())
                    if match:
                        dep_list = match.group(1)
                        # Split by comma or whitespace to support multiple dependencies
                        for dep in re.split(r'[,\s]+', dep_list):
                            dep = dep.strip()
                            if dep:
                                # Ensure .tex extension
                                if not dep.endswith('.tex'):
                                    dep += '.tex'
                                deps.add(dep)
        except Exception as e:
            logger.warning(f"Could not parse dependencies from {file_path}: {e}")
        return deps

    def _extract_metadata(self, file_path: Path) -> Dict:
        """Extract metadata from appendix file."""
        metadata = {
            'filename': file_path.name,
            'stem': file_path.stem,
            'title': None,
            'label': None,
        }

        # Try to extract chapter title and label
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

                # Look for \section or \chapter commands
                title_match = re.search(r'\\(?:chapter|section)\{([^}]+)\}', content)
                if title_match:
                    metadata['title'] = title_match.group(1)

                # Look for \label commands
                label_match = re.search(r'\\label\{([^}]+)\}', content)
                if label_match:
                    metadata['label'] = label_match.group(1)
        except Exception:
            pass

        return metadata

    def resolve_dependencies(self, required_files: Set[str]) -> List[str]:
        """Resolve dependencies for a set of required appendix files.

        Args:
            required_files: Set of appendix filenames that are required

        Returns:
            Ordered list of appendix filenames including all dependencies
        """
        resolved = []
        visited = set()

        def visit(filename: str):
            if filename in visited:
                return
            visited.add(filename)

            # Visit dependencies first (depth-first)
            if filename in self.dependencies:
                for dep in self.dependencies[filename]:
                    if dep in self.dependencies or self.appendix_dir.joinpath(dep).exists():
                        visit(dep)

            # Add this file after its dependencies
            if filename not in resolved:
                resolved.append(filename)

        # Process each required file
        for filename in required_files:
            visit(filename)

        return resolved

    def get_appendix_info(self, filename: str) -> Optional[Dict]:
        """Get metadata for an appendix file."""
        return self.appendix_metadata.get(filename)

    def generate_appendix_section(self, required_files: Set[str]) -> str:
        """Generate LaTeX appendix section with resolved dependencies.

        Args:
            required_files: Set of appendix filenames that are required

        Returns:
            LaTeX code for the appendix section
        """
        if not required_files:
            return ""

        # Resolve dependencies
        ordered_files = self.resolve_dependencies(required_files)

        if not ordered_files:
            return ""

        latex_parts = ["\\appendix\n"]

        for filename in ordered_files:
            metadata = self.get_appendix_info(filename)
            stem = Path(filename).stem

            # Generate chapter entry
            if metadata and metadata.get('title'):
                title = metadata['title']
            else:
                # Generate title from filename
                title = stem.replace('_', ' ').title()

            latex_parts.append(f"\\chapter{{{title}}}\n")

            # Generate label automatically from filename (same logic as in generators.py)
            auto_label = "appendix:" + stem.replace('-', '').replace('_', '').replace(' ', '')

            # Use label from file metadata if it exists, otherwise use auto-generated
            if metadata and metadata.get('label'):
                latex_parts.append(f"\\label{{{metadata['label']}}}\n")
            else:
                latex_parts.append(f"\\label{{{auto_label}}}\n")

            # Include the file
            latex_parts.append(f"\\include{{appendixes/{stem}}}\n")
            latex_parts.append("\n")

        return "".join(latex_parts)

    def list_available_appendixes(self) -> List[Dict]:
        """List all available appendix files with their metadata."""
        result = []
        for filename, metadata in self.appendix_metadata.items():
            info = metadata.copy()
            info['dependencies'] = list(self.dependencies.get(filename, []))
            result.append(info)
        return result