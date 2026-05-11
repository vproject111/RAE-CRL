import csv
import io
from typing import Dict, Any, Optional
from apps.crl.core.models import BaseArtifact, ArtifactType, ArtifactStatus, ArtifactVisibility

class IngestionService:
    """Service for parsing raw data files and converting them into Research Observations."""

    @staticmethod
    def parse_csv(content: str, filename: str) -> Dict[str, Any]:
        """Parses a CSV string and returns summary metadata."""
        f = io.StringIO(content)
        reader = csv.DictReader(f)
        data = list(reader)
        
        return {
            "filename": filename,
            "format": "csv",
            "row_count": len(data),
            "columns": list(data[0].keys()) if data else [],
            "preview": data[:3] if data else []
        }

    @staticmethod
    def create_observation_from_file(filename: str, content: str, project: str, author: str = "auto-bridge") -> BaseArtifact:
        """Creates an Observation artifact based on file content analysis."""
        
        metadata = {}
        summary = f"Automated ingestion of {filename}.\n"
        
        if filename.endswith(".csv"):
            metadata = IngestionService.parse_csv(content, filename)
            summary += f"Detected CSV with {metadata.get('row_count')} rows and columns: {', '.join(metadata.get('columns', []))}."
        else:
            metadata = {"filename": filename, "format": "txt", "size": len(content)}
            summary += f"Text file ingested ({len(content)} characters)."

        return BaseArtifact(
            type=ArtifactType.OBSERVATION,
            title=f"Data Import: {filename}",
            description=summary,
            project=project,
            status=ArtifactStatus.ACTIVE,
            visibility=ArtifactVisibility.PRIVATE,
            author=author,
            metadata_blob=metadata
        )
