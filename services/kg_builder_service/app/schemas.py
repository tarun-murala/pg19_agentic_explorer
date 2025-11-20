from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class Entity(BaseModel):
    name: str
    type: str = Field(default="unknown")
    description: Optional[str] = None
    aliases: List[str] = []


class Relation(BaseModel):
    source: str
    target: str
    type: str = Field(default="related_to")
    description: Optional[str] = None


class KGBuildRequest(BaseModel):
    book_id: int
    book_title: Optional[str] = None
    chunk_id: int
    chunk_index: Optional[int] = None
    chunk_content: str


class KGBuildResponse(BaseModel):
    book_id: int
    chunk_id: int
    entities_created: int
    relations_created: int
    entities: List[Entity]
    relations: List[Relation]


class EntityNode(BaseModel):
    name: str
    type: str
    description: Optional[str] = None
    mentions: int = 0


class RelationEdge(BaseModel):
    source: str
    target: str
    type: str
    description: Optional[str] = None
    chunk_ids: List[int] = []


class KGQueryResponse(BaseModel):
    book_id: Optional[int]
    chunk_id: Optional[int]
    entities: List[EntityNode]
    relations: List[RelationEdge]
