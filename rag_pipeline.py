from pathlib import Path

import fitz
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer


# ============================================================
# CONFIGURATION
# ============================================================

DOCUMENTS_DIR = Path("documents")
INDEX_DIR = Path("faiss_store")

INDEX_FILE = INDEX_DIR / "corporate_documents.index"
CHUNKS_FILE = INDEX_DIR / "chunks.txt"

EMBEDDING_MODEL = "all-MiniLM-L6-v2"

CHUNK_SIZE = 350
CHUNK_OVERLAP = 50

DEFAULT_TOP_K = 2


# ============================================================
# MODEL CACHE
# ============================================================

_embedding_model = None


def get_embedding_model():
    """
    Load the embedding model only once per Python process.
    """

    global _embedding_model

    if _embedding_model is None:

        print(
            "Loading embedding model..."
        )

        _embedding_model = SentenceTransformer(
            EMBEDDING_MODEL
        )

    return _embedding_model


# ============================================================
# FAISS / CHUNK CACHE
# ============================================================

_faiss_index = None
_chunks = None


def get_faiss_index():
    """
    Load the FAISS index only once per Python process.
    """

    global _faiss_index

    if _faiss_index is None:

        if not INDEX_FILE.exists():

            raise FileNotFoundError(
                "FAISS index was not found. "
                "Run build_faiss_index() first."
            )

        print(
            "Loading FAISS index..."
        )

        _faiss_index = faiss.read_index(
            str(INDEX_FILE)
        )

    return _faiss_index


def get_chunks():
    """
    Load document chunks only once per Python process.
    """

    global _chunks

    if _chunks is None:

        _chunks = load_chunks()

    return _chunks


# ============================================================
# PDF TEXT EXTRACTION
# ============================================================

def extract_text_from_pdf(pdf_path):
    """
    Extract text from a PDF using PyMuPDF.
    """

    document = fitz.open(
        pdf_path
    )

    pages = []

    for page in document:

        text = page.get_text(
            "text"
        )

        if text.strip():

            pages.append(
                text
            )

    document.close()

    return "\n".join(
        pages
    )


# ============================================================
# TEXT CHUNKING
# ============================================================

import re


def _split_into_sentences(text):
    """
    Split text into sentences using simple punctuation-based
    boundaries. Good enough for policy-document prose without
    pulling in a full NLP dependency.
    """

    sentences = re.split(
        r"(?<=[.!?])\s+",
        text
    )

    return [
        sentence.strip()
        for sentence in sentences
        if sentence.strip()
    ]


def create_chunks(
    text,
    chunk_size=CHUNK_SIZE,
    overlap=CHUNK_OVERLAP
):
    """
    Split text into overlapping chunks, breaking only at
    sentence boundaries so each chunk reads as a clean,
    self-contained passage instead of being cut mid-sentence.
    """

    text = " ".join(
        text.split()
    )

    sentences = _split_into_sentences(text)

    chunks = []

    current_sentences = []
    current_length = 0

    for sentence in sentences:

        sentence_length = len(sentence) + 1

        if current_sentences and (
            current_length + sentence_length > chunk_size
        ):

            chunks.append(
                " ".join(current_sentences).strip()
            )

            # Carry the last sentence forward as overlap so
            # context isn't lost at chunk boundaries.
            overlap_sentences = []
            overlap_length = 0

            for prev_sentence in reversed(current_sentences):

                overlap_length += len(prev_sentence) + 1

                overlap_sentences.insert(0, prev_sentence)

                if overlap_length >= overlap:
                    break

            current_sentences = overlap_sentences
            current_length = sum(
                len(s) + 1 for s in current_sentences
            )

        current_sentences.append(sentence)
        current_length += sentence_length

    if current_sentences:

        chunks.append(
            " ".join(current_sentences).strip()
        )

    return chunks


# ============================================================
# LOAD CORPORATE DOCUMENTS
# ============================================================

def load_documents():
    """
    Load all corporate PDF documents and
    create chunks.
    """

    if not DOCUMENTS_DIR.exists():

        raise FileNotFoundError(
            "documents folder was not found."
        )

    pdf_files = list(
        DOCUMENTS_DIR.glob("*.pdf")
    )

    if not pdf_files:

        raise ValueError(
            "No PDF documents were found."
        )

    all_chunks = []

    for pdf_file in pdf_files:

        print(
            f"Reading: {pdf_file.name}"
        )

        text = extract_text_from_pdf(
            pdf_file
        )

        chunks = create_chunks(
            text
        )

        for chunk in chunks:

            all_chunks.append({
                "source": pdf_file.name,
                "text": chunk
            })

    if not all_chunks:

        raise ValueError(
            "No text could be extracted "
            "from the corporate documents."
        )

    return all_chunks


# ============================================================
# BUILD FAISS INDEX
# ============================================================

def build_faiss_index():
    """
    Build the FAISS index.

    Run this only when corporate documents
    are added or changed.
    """

    global _faiss_index
    global _chunks

    print(
        "\n=============================================="
    )

    print(
        "\n        BUILDING CORPORATE RAG INDEX"
    )

    print(
        "\n=============================================="
    )

    documents = load_documents()

    texts = [
        item["text"]
        for item in documents
    ]

    print(
        f"\nTotal chunks: {len(texts)}"
    )

    model = get_embedding_model()

    print(
        "\nCreating embeddings..."
    )

    embeddings = model.encode(
        texts,
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=True
    )

    embeddings = np.asarray(
        embeddings,
        dtype="float32"
    )

    dimension = embeddings.shape[1]

    print(
        f"\nEmbedding dimension: {dimension}"
    )

    index = faiss.IndexFlatIP(
        dimension
    )

    index.add(
        embeddings
    )

    INDEX_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    faiss.write_index(
        index,
        str(INDEX_FILE)
    )

    with open(
        CHUNKS_FILE,
        "w",
        encoding="utf-8"
    ) as file:

        for item in documents:

            file.write(
                item["source"]
            )

            file.write(
                "\n"
            )

            file.write(
                item["text"]
            )

            file.write(
                "\n---CHUNK---\n"
            )

    # Update in-memory cache
    _faiss_index = index
    _chunks = documents

    print(
        "\nFAISS index created successfully."
    )

    print(
        f"Index: {INDEX_FILE}"
    )

    print(
        f"Chunks: {CHUNKS_FILE}"
    )

    print(
        "\n=============================================="
    )


# ============================================================
# LOAD STORED CHUNKS
# ============================================================

def load_chunks():
    """
    Load stored chunks and source information.
    """

    if not CHUNKS_FILE.exists():

        raise FileNotFoundError(
            "FAISS chunks file was not found. "
            "Build the index first."
        )

    with open(
        CHUNKS_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        content = file.read()

    raw_chunks = content.split(
        "\n---CHUNK---\n"
    )

    chunks = []

    for item in raw_chunks:

        item = item.strip()

        if not item:

            continue

        lines = item.split(
            "\n",
            1
        )

        source = lines[0].strip()

        text = ""

        if len(lines) > 1:

            text = lines[1].strip()

        chunks.append({
            "source": source,
            "text": text
        })

    return chunks


# ============================================================
# RETRIEVE DOCUMENTS
# ============================================================

def retrieve_documents(
    query,
    top_k=DEFAULT_TOP_K
):
    """
    Retrieve the most relevant corporate
    document chunks.

    Runtime operations:

    Question
       ↓
    Embedding
       ↓
    FAISS search
       ↓
    Top K chunks
    """

    index = get_faiss_index()

    chunks = get_chunks()

    model = get_embedding_model()

    query_embedding = model.encode(
        [query],
        convert_to_numpy=True,
        normalize_embeddings=True
    )

    query_embedding = np.asarray(
        query_embedding,
        dtype="float32"
    )

    actual_top_k = min(
        top_k,
        index.ntotal
    )

    scores, indices = index.search(
        query_embedding,
        actual_top_k
    )

    results = []

    for score, index_number in zip(
        scores[0],
        indices[0]
    ):

        if index_number == -1:

            continue

        if index_number >= len(chunks):

            continue

        results.append({
            "source": chunks[index_number]["source"],
            "text": chunks[index_number]["text"],
            "score": float(score)
        })

    return results


# ============================================================
# BUILD RAG CONTEXT
# ============================================================

def build_rag_context(
    query,
    top_k=DEFAULT_TOP_K
):
    """
    Build clean context for the Document/RAG Agent.
    """

    results = retrieve_documents(
        query,
        top_k
    )

    if not results:

        return (
            "No relevant corporate document "
            "information was found."
        )

    context_parts = []

    for number, result in enumerate(
        results,
        start=1
    ):

        context_parts.append(
            f"""
SOURCE {number}: {result['source']}

RETRIEVED CONTENT:
{result['text']}
"""
        )

    return "\n".join(
        context_parts
    )


# ============================================================
# SIMPLE RETRIEVAL TEST
# ============================================================

def test_retrieval():
    """
    Test FAISS retrieval without AutoGen.
    """

    question = input(
        "\nEnter a corporate policy question: "
    )

    results = retrieve_documents(
        question,
        top_k=DEFAULT_TOP_K
    )

    print(
        "\n=============================================="
    )

    print(
        "\n        RETRIEVED CORPORATE INFORMATION"
    )

    print(
        "\n=============================================="
    )

    for number, result in enumerate(
        results,
        start=1
    ):

        print(
            f"\nResult {number}"
        )

        print(
            f"Source: {result['source']}"
        )

        print(
            f"Score: {result['score']:.4f}"
        )

        print(
            f"\n{result['text']}"
        )

        print(
            "\n----------------------------------------------"
        )


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    print(
        "\n=============================================="
    )

    print(
        "\n        CORPORATE RAG PIPELINE"
    )

    print(
        "\n=============================================="
    )

    print(
        "\nBuilding index..."
    )

    build_faiss_index()

    test_retrieval()