"""
API contract schemas. Must stay in sync with frontend/src/api.ts and AGENTS.md.
"""

from typing import Optional

from pydantic import BaseModel, Field


class ProfileRepo(BaseModel):
    """Single repo in ProfileData.repos."""
    name: str
    url: str
    description: Optional[str] = None
    stars: Optional[int] = None
    forks: Optional[int] = None
    language: Optional[str] = None


class ProfileData(BaseModel):
    """GET /api/profile/{username} response. Frontend expects these exact field names."""
    username: str
    name: Optional[str] = None
    bio: Optional[str] = None
    followers: Optional[int] = None
    public_repos: Optional[int] = None
    top_languages: list[tuple[str, int]] = Field(
        default_factory=list,
        description="List of [language_name, bytes] tuples",
    )
    repos: list[ProfileRepo] = Field(default_factory=list)

    class Config:
        # Allow extra fields (e.g. avatar_url, profile_url, stats, languages) for backward compatibility
        extra = "allow"


class ReadmeConfig(BaseModel):
    """Configuration for README generation. POST /api/generate body.config."""
    sections: list[str] = Field(default_factory=list)
    theme: str = "light"
    layout: str = "default"


class GeneratedReadme(BaseModel):
    """POST /api/generate response."""
    markdown: str = ""
    assets: Optional[dict[str, str]] = None
