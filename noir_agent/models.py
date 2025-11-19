"""Pydantic data models used across Noir API Mapper."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class NoirParam(BaseModel):
    """Represents a parameter reported by OWASP Noir."""

    name: str
    param_type: str = Field(alias="type")
    extra: Dict[str, Any] = Field(default_factory=dict)


class NoirEndpoint(BaseModel):
    """Endpoint information discovered by OWASP Noir."""

    method: str
    url: str
    params: List[NoirParam] = Field(default_factory=list)
    sources: List[str] = Field(default_factory=list)


class ApiParam(BaseModel):
    name: str
    in_: str = Field(alias="in")
    required: bool
    type: str = "string"
    description: str = ""


class ApiResponse(BaseModel):
    status: int
    contentType: str = "application/json"
    schema: Dict[str, Any] = Field(default_factory=dict)
    example: Optional[Any] = None


class ApiEndpoint(BaseModel):
    method: str
    path: str
    summary: str
    description: str
    pathParams: List[ApiParam] = Field(default_factory=list)
    queryParams: List[ApiParam] = Field(default_factory=list)
    headers: List[ApiParam] = Field(default_factory=list)
    requestBody: Optional[Dict[str, Any]] = None
    responses: List[ApiResponse] = Field(default_factory=list)
    source: Dict[str, Any] = Field(default_factory=dict)


class ApiCollection(BaseModel):
    title: str
    version: str
    baseUrl: str
    endpoints: List[ApiEndpoint] = Field(default_factory=list)


__all__ = [
    "NoirParam",
    "NoirEndpoint",
    "ApiParam",
    "ApiResponse",
    "ApiEndpoint",
    "ApiCollection",
]
