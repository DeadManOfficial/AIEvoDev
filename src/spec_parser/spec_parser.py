"""
Specification Parser - Parses GSD YAML specification files.
"""
import os
import yaml
from typing import Dict, Any


class SpecificationParser:
    """Parses GSD-defined YAML specification files."""

    def load_spec(self, file_path: str) -> Dict[str, Any]:
        """
        Load and parse a YAML specification file.

        Args:
            file_path: Path to the YAML specification file.

        Returns:
            Dictionary representing the parsed YAML content.

        Raises:
            FileNotFoundError: If the file does not exist.
            yaml.YAMLError: If there is an error parsing the YAML.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Specification file not found: {file_path}")

        with open(file_path, 'r', encoding='utf-8') as f:
            try:
                spec = yaml.safe_load(f)
                if not isinstance(spec, dict):
                    raise yaml.YAMLError("YAML content is not a dictionary.")
                return spec
            except yaml.YAMLError as e:
                raise yaml.YAMLError(f"Error parsing YAML file {file_path}: {e}")
