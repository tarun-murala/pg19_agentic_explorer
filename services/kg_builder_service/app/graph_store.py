from __future__ import annotations

from typing import Iterable, List

from neo4j import GraphDatabase, Transaction

from .config import Settings, get_settings
from .schemas import Entity, KGQueryResponse, Relation


class GraphStore:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self._driver = GraphDatabase.driver(
            self.settings.neo4j_uri,
            auth=(self.settings.neo4j_user, self.settings.neo4j_password),
        )

    def close(self) -> None:
        self._driver.close()

    def upsert(self, *, book_id: int, book_title: str | None, chunk_id: int, chunk_index: int | None,
               entities: List[Entity], relations: List[Relation]) -> None:
        with self._driver.session() as session:
            session.execute_write(
                self._write_graph,
                book_id,
                book_title,
                chunk_id,
                chunk_index,
                [entity.dict() for entity in entities],
                [relation.dict() for relation in relations],
            )

    @staticmethod
    def _write_graph(
        tx: Transaction,
        book_id: int,
        book_title: str | None,
        chunk_id: int,
        chunk_index: int | None,
        entities: List[dict],
        relations: List[dict],
    ) -> None:
        tx.run(
            """
            MERGE (b:Book {book_id: $book_id})
              ON CREATE SET b.title = $book_title
              ON MATCH SET b.title = COALESCE($book_title, b.title)
            MERGE (c:Chunk {chunk_id: $chunk_id})
              SET c.book_id = $book_id, c.chunk_index = $chunk_index
            MERGE (b)-[:HAS_CHUNK]->(c)
            """,
            book_id=book_id,
            book_title=book_title,
            chunk_id=chunk_id,
            chunk_index=chunk_index,
        )

        for entity in entities:
            tx.run(
                """
                MERGE (e:Entity {name: $name})
                  SET e.type = COALESCE($type, e.type),
                      e.description = COALESCE($description, e.description)
                MERGE (c:Chunk {chunk_id: $chunk_id})
                MERGE (c)-[m:MENTIONS]->(e)
                  ON CREATE SET m.book_id = $book_id
                  ON MATCH SET m.book_id = $book_id
                SET m.chunk_id = $chunk_id
                """,
                name=entity.get("name"),
                type=entity.get("type"),
                description=entity.get("description"),
                chunk_id=chunk_id,
                book_id=book_id,
            )

        for relation in relations:
            tx.run(
                """
                MERGE (source:Entity {name: $source})
                MERGE (target:Entity {name: $target})
                MERGE (source)-[r:RELATION {chunk_id: $chunk_id}]->(target)
                  SET r.type = $type,
                      r.description = $description,
                      r.book_id = $book_id
                """,
                source=relation.get("source"),
                target=relation.get("target"),
                type=relation.get("type"),
                description=relation.get("description"),
                chunk_id=chunk_id,
                book_id=book_id,
            )

    def query(self, *, book_id: int | None = None, chunk_id: int | None = None) -> KGQueryResponse:
        with self._driver.session() as session:
            entities = session.execute_read(self._fetch_entities, book_id, chunk_id)
            relations = session.execute_read(self._fetch_relations, book_id, chunk_id)
        return KGQueryResponse(book_id=book_id, chunk_id=chunk_id, entities=entities, relations=relations)

    @staticmethod
    def _fetch_entities(tx: Transaction, book_id: int | None, chunk_id: int | None) -> List[dict]:
        if chunk_id is not None:
            query = (
                """
                MATCH (c:Chunk {chunk_id: $chunk_id})-[:MENTIONS]->(e:Entity)
                OPTIONAL MATCH (e)<-[m:MENTIONS]-(:Chunk)
                RETURN e.name AS name, e.type AS type, e.description AS description, count(m) AS mentions
                ORDER BY mentions DESC, name ASC
                """
            )
            params = {"chunk_id": chunk_id}
        else:
            query = (
                """
                MATCH (b:Book {book_id: $book_id})-[:HAS_CHUNK]->(:Chunk)-[:MENTIONS]->(e:Entity)
                OPTIONAL MATCH (e)<-[m:MENTIONS]-(:Chunk)
                RETURN e.name AS name, e.type AS type, e.description AS description, count(m) AS mentions
                ORDER BY mentions DESC, name ASC
                """
            )
            params = {"book_id": book_id}
        records = tx.run(query, **params)
        return [dict(record) for record in records]

    @staticmethod
    def _fetch_relations(tx: Transaction, book_id: int | None, chunk_id: int | None) -> List[dict]:
        filter_clause = ""
        params: dict = {}
        if chunk_id is not None:
            filter_clause = "WHERE r.chunk_id = $chunk_id"
            params["chunk_id"] = chunk_id
        elif book_id is not None:
            filter_clause = "WHERE r.book_id = $book_id"
            params["book_id"] = book_id
        query = f"""
            MATCH (source:Entity)-[r:RELATION]->(target:Entity)
            {filter_clause}
            RETURN source.name AS source, target.name AS target, r.type AS type, r.description AS description,
                   collect(r.chunk_id) AS chunk_ids
            ORDER BY size(chunk_ids) DESC, type ASC
        """
        records = tx.run(query, **params)
        return [dict(record) for record in records]
