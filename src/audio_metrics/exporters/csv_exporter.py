"""
CSV Exporter Module
==================
Export metrics to CSV format.
"""

import csv
from pathlib import Path
from typing import Any, Dict, List

from core.logger import get_logger

logger = get_logger(__name__)


class CSVExporter:
    """Export metrics to CSV format."""

    def export(self, metrics: Dict[str, Any], output_path: str) -> str:
        """
        Export metrics to CSV file.

        Args:
            metrics: Analysis metrics dictionary
            output_path: Output file path

        Returns:
            Path to exported file
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Flatten metrics for CSV
        rows = self._flatten_metrics(metrics)

        # Write CSV
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            if rows:
                writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows(rows)

        logger.info("CSV exported", path=str(output_path), rows=len(rows))
        return str(output_path)

    def _flatten_metrics(self, metrics: Dict[str, Any], parent_key: str = "") -> List[Dict[str, Any]]:
        """
        Flatten nested metrics into list of rows.

        Args:
            metrics: Nested metrics dictionary
            parent_key: Parent key prefix

        Returns:
            List of flattened metric dictionaries
        """
        rows = []

        # Handle single record
        flat = {}
        self._flatten_dict(metrics, flat, parent_key)

        # Convert to list format (for multiple files support)
        rows.append(flat)

        return rows

    def _flatten_dict(self, d: Dict[str, Any], result: Dict[str, Any], parent_key: str = "") -> None:
        """
        Recursively flatten dictionary.

        Args:
            d: Source dictionary
            result: Target flattened dictionary
            parent_key: Parent key prefix
        """
        for key, value in d.items():
            new_key = f"{parent_key}_{key}" if parent_key else key

            if isinstance(value, dict):
                self._flatten_dict(value, result, new_key)
            elif isinstance(value, list):
                # Convert list to string representation
                if value and isinstance(value[0], dict):
                    # List of dicts - flatten each
                    for i, item in enumerate(value):
                        self._flatten_dict(item, result, f"{new_key}_{i}")
                else:
                    result[new_key] = "; ".join(str(v) for v in value)
            else:
                result[new_key] = value


class BatchCSVExporter:
    """Export batch analysis results to CSV."""

    def export_batch(self, results: List[Dict[str, Any]], output_path: str) -> str:
        """
        Export batch results to CSV.

        Args:
            results: List of analysis results
            output_path: Output file path

        Returns:
            Path to exported file
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if not results:
            logger.warning("No results to export")
            return str(output_path)

        # Flatten each result
        rows = []
        for result in results:
            flat = {}
            self._flatten_dict(result, flat)
            rows.append(flat)

        # Get all unique keys
        fieldnames = set()
        for row in rows:
            fieldnames.update(row.keys())
        fieldnames = sorted(fieldnames)

        # Write CSV
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

        logger.info("Batch CSV exported", path=str(output_path), rows=len(rows))
        return str(output_path)

    def _flatten_dict(self, d: Dict[str, Any], result: Dict[str, Any], parent_key: str = "") -> None:
        """Recursively flatten dictionary."""
        for key, value in d.items():
            new_key = f"{parent_key}_{key}" if parent_key else key

            if isinstance(value, dict):
                self._flatten_dict(value, result, new_key)
            elif isinstance(value, list):
                if value and isinstance(value[0], dict):
                    for i, item in enumerate(value):
                        self._flatten_dict(item, result, f"{new_key}_{i}")
                else:
                    result[new_key] = "; ".join(str(v) for v in value)
            else:
                result[new_key] = value
