from .models import Book, Chunk
from .schemas import BookRead, ChunkDetail, ChunkSummary


def to_book_read(book: Book) -> BookRead:
    return BookRead(
        id=book.id,
        pg_id=book.pg_id,
        title=book.title,
        author=book.author,
        language=book.language,
        published_year=book.published_year,
        source_path=book.source_path,
        checksum=book.checksum,
        word_count=book.word_count,
        chunk_count=book.chunk_count,
        created_at=book.created_at,
    )


def to_chunk_summary(chunk: Chunk) -> ChunkSummary:
    return ChunkSummary(
        id=chunk.id,
        book_id=chunk.book_id,
        chunk_index=chunk.chunk_index,
        start_char=chunk.start_char,
        end_char=chunk.end_char,
    )


def to_chunk_detail(chunk: Chunk) -> ChunkDetail:
    return ChunkDetail(
        id=chunk.id,
        book_id=chunk.book_id,
        chunk_index=chunk.chunk_index,
        start_char=chunk.start_char,
        end_char=chunk.end_char,
        content=chunk.content,
    )
