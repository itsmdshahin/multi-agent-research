"""
PDF Ingestion Service.
Handles text extraction (with OCR fallback), chunking, embedding generation,
and storage in Qdrant. Supports both digital and scanned PDFs.
"""
import os
import re
import uuid
from dataclasses import dataclass
from typing import List, Optional, Tuple

import fitz  # PyMuPDF
import pdfplumber

from core.config import settings
from core.logging import get_logger
from services.embeddings import embedding_service

logger = get_logger(__name__)


@dataclass
class PageContent:
    page_number: int
    text: str
    is_ocr: bool = False


@dataclass
class DocumentChunk:
    chunk_index: int
    text: str
    page_number: int
    document_id: str
    document_name: str
    total_pages: int
    embedding: Optional[List[float]] = None


class PDFExtractor:
    """Extract text from PDFs using PyMuPDF with OCR fallback via pdfplumber."""

    MIN_TEXT_LENGTH = 50  # below this, assume page needs OCR

    async def extract_pages(self, file_path: str) -> Tuple[List[PageContent], dict]:
        """
        Extract text from all pages. Returns pages and document metadata.
        """
        pages: List[PageContent] = []
        meta: dict = {}

        try:
            # First pass: PyMuPDF (fast)
            with fitz.open(file_path) as doc:
                meta = {
                    "title": doc.metadata.get("title", ""),
                    "author": doc.metadata.get("author", ""),
                    "subject": doc.metadata.get("subject", ""),
                    "creator": doc.metadata.get("creator", ""),
                    "total_pages": len(doc),
                }

                for page_num, page in enumerate(doc, start=1):
                    text = page.get_text("text")
                    if text and len(text.strip()) >= self.MIN_TEXT_LENGTH:
                        pages.append(PageContent(
                            page_number=page_num,
                            text=self._clean_text(text),
                            is_ocr=False,
                        ))
                    else:
                        # Fallback: pdfplumber for this page
                        pages.append(PageContent(
                            page_number=page_num,
                            text="",  # will fill below
                            is_ocr=True,
                        ))

            # Second pass: pdfplumber for OCR-needed pages
            ocr_pages = [p for p in pages if p.is_ocr]
            if ocr_pages:
                with pdfplumber.open(file_path) as pdf:
                    for page_content in ocr_pages:
                        idx = page_content.page_number - 1
                        if idx < len(pdf.pages):
                            text = pdf.pages[idx].extract_text() or ""
                            page_content.text = self._clean_text(text)

            # Final fallback: pytesseract OCR (if available)
            still_empty = [p for p in pages if not p.text.strip()]
            if still_empty:
                try:
                    import pytesseract
                    from PIL import Image

                    with fitz.open(file_path) as doc:
                        for page_content in still_empty:
                            idx = page_content.page_number - 1
                            page = doc[idx]
                            pix = page.get_pixmap(dpi=200)
                            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                            text = pytesseract.image_to_string(img)
                            page_content.text = self._clean_text(text)
                            page_content.is_ocr = True
                except (ImportError, Exception) as e:
                    logger.warning("OCR unavailable", error=str(e))

        except Exception as e:
            logger.error("PDF extraction failed", file=file_path, error=str(e))
            raise

        return pages, meta

    @staticmethod
    def _clean_text(text: str) -> str:
        """Remove excessive whitespace and fix encoding artifacts."""
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'[^\x00-\x7F]+', ' ', text)  # strip non-ASCII
        return text.strip()


class TextChunker:
    """
    Split extracted text into overlapping chunks suitable for embedding.
    Uses sentence-aware splitting to preserve context.
    """

    def __init__(
        self,
        chunk_size: int = settings.CHUNK_SIZE,
        chunk_overlap: int = settings.CHUNK_OVERLAP,
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_pages(
        self,
        pages: List[PageContent],
        document_id: str,
        document_name: str,
    ) -> List[DocumentChunk]:
        """Chunk all pages of a document into overlapping text chunks."""
        total_pages = len(pages)
        all_chunks: List[DocumentChunk] = []
        chunk_index = 0

        for page in pages:
            if not page.text.strip():
                continue

            page_chunks = self._split_text(page.text)

            for chunk_text in page_chunks:
                all_chunks.append(DocumentChunk(
                    chunk_index=chunk_index,
                    text=chunk_text,
                    page_number=page.page_number,
                    document_id=document_id,
                    document_name=document_name,
                    total_pages=total_pages,
                ))
                chunk_index += 1

        return all_chunks

    def _split_text(self, text: str) -> List[str]:
        """Split text into chunks with overlap."""
        words = text.split()
        chunks: List[str] = []

        if not words:
            return chunks

        start = 0
        while start < len(words):
            end = min(start + self.chunk_size, len(words))
            chunk = " ".join(words[start:end])
            if chunk.strip():
                chunks.append(chunk)
            if end == len(words):
                break
            start += self.chunk_size - self.chunk_overlap

        return chunks


class PDFIngestionService:
    """Orchestrates the full PDF ingestion pipeline."""

    def __init__(self):
        self.extractor = PDFExtractor()
        self.chunker = TextChunker()

    async def ingest(
        self,
        file_path: str,
        document_id: str,
        document_name: str,
        user_id: str,
        vector_store,  # VectorStore instance
    ) -> dict:
        """
        Full ingestion pipeline:
        1. Extract text from PDF
        2. Chunk the text
        3. Generate embeddings
        4. Store in Qdrant
        Returns metadata about the ingestion.
        """
        logger.info("Starting PDF ingestion", document_id=document_id, file=document_name)

        # Step 1: Extract text
        pages, doc_meta = await self.extractor.extract_pages(file_path)
        total_text = sum(len(p.text) for p in pages)
        word_count = sum(len(p.text.split()) for p in pages)

        logger.info(
            "Text extracted",
            document_id=document_id,
            pages=len(pages),
            words=word_count,
        )

        # Step 2: Chunk
        chunks = self.chunker.chunk_pages(pages, document_id, document_name)
        logger.info("Text chunked", document_id=document_id, chunks=len(chunks))

        if not chunks:
            raise ValueError("No text could be extracted from the document")

        # Step 3: Generate embeddings in batches
        texts = [c.text for c in chunks]
        embeddings = await embedding_service.embed_batch(texts)

        # Step 4: Attach embeddings and upsert to Qdrant
        chunk_dicts = []
        for chunk, embedding in zip(chunks, embeddings):
            chunk_dicts.append({
                "text": chunk.text,
                "embedding": embedding,
                "page_number": chunk.page_number,
                "chunk_index": chunk.chunk_index,
                "document_name": chunk.document_name,
                "total_pages": chunk.total_pages,
            })

        upserted = await vector_store.upsert_chunks(document_id, user_id, chunk_dicts)

        logger.info("PDF ingestion complete", document_id=document_id, chunks_stored=upserted)

        return {
            "document_id": document_id,
            "page_count": len(pages),
            "word_count": word_count,
            "chunk_count": upserted,
            "doc_meta": doc_meta,
            "has_ocr_pages": any(p.is_ocr for p in pages),
        }


# Singleton
pdf_ingestion_service = PDFIngestionService()
