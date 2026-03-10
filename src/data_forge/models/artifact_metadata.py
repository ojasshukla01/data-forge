"""Artifact metadata and retention policy models."""

from typing import Any

from pydantic import BaseModel, Field


class ArtifactMetadata(BaseModel):
    """Metadata for a single artifact file."""

    artifact_id: str = ""
    run_id: str
    artifact_type: str = "dataset"
    file_path: str
    file_name: str
    file_size: int = 0
    mime_type: str | None = None
    checksum: str | None = None
    created_at: float | None = None
    archived_at: float | None = None
    deleted_at: float | None = None
    pinned: bool = False
    tags: list[str] = Field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump()


class RetentionPolicy(BaseModel):
    """Policy for run/artifact retention and cleanup."""

    max_run_count: int = 100
    max_age_days: float | None = None
    max_storage_mb: float | None = None
    exclude_statuses: list[str] = Field(default_factory=lambda: ["running", "queued"])
    exclude_run_types: list[str] = Field(default_factory=list)
    exclude_pinned: bool = True
    exclude_archived: bool = False  # If True, never delete archived runs
