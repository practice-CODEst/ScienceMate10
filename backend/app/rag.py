
from pathlib import Path
import re

import chromadb
import pymupdf
from sentence_transformers import SentenceTransformer

ROOT = Path(__file__).resolve().parents[2]
PDF_PATH = ROOT / "textbooks" / "Science10.pdf"
DB_PATH = ROOT / "data" / "chroma"

client = chromadb.PersistentClient(path=str(DB_PATH))
model = None

# Printed textbook page numbers; PDF pages are 8 pages ahead.
CHAPTERS = [
    ("Laws of Motion", 1),
    ("Optics", 16),
    ("Thermal Physics", 32),
    ("Electricity", 42),
    ("Acoustics", 59),
    ("Nuclear Physics", 74),
    ("Atoms and Molecules", 91),
    ("Periodic Classification of Elements", 106),
    ("Solutions", 124),
    ("Types of Chemical Reactions", 137),
    ("Carbon and its Compounds", 155),
    ("Plant Anatomy and Plant Physiology", 173),
    ("Structural Organisation of Animals", 187),
    ("Transportation in Plants and Circulation in Animals", 200),
    ("Nervous System", 218),
    ("Plant and Animal Hormones", 229),
    ("Reproduction in Plants and Animals", 243),
    ("Genetics", 261),
    ("Origin and Evolution of Life", 274),
    ("Breeding and Biotechnology", 286),
    ("Health and Diseases", 300),
    ("Environmental Management", 315),
    ("Visual Communication", 329),
]


def get_model():
    global model
    if model is None:
        model = SentenceTransformer(
            "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
        )
    return model


def get_collection(subject):
    name = re.sub(r"[^a-zA-Z0-9_-]", "_", subject.lower())[:40]
    return client.get_collection(name + "_english")


def index_textbook(subject="Science"):
    if subject != "Science":
        raise ValueError("Only the Science textbook is currently configured.")
    if not PDF_PATH.exists():
        raise FileNotFoundError(f"Textbook not found: {PDF_PATH}")

    collection = client.get_or_create_collection("science_english")
    pdf = pymupdf.open(str(PDF_PATH))
    ids, documents, metadata = [], [], []

    starts = [(name, page + 8) for name, page in CHAPTERS]

    for pdf_page, page in enumerate(pdf, start=1):
        chapter = None
        for i, (name, start_page) in enumerate(starts):
            end_page = (
                starts[i + 1][1] - 1
                if i + 1 < len(starts)
                else 341
            )
            if start_page <= pdf_page <= end_page:
                chapter = name
                break

        if chapter is None:
            continue

        text = re.sub(r"\s+", " ", page.get_text()).strip()

        for start in range(0, len(text), 850):
            chunk = text[start:start + 1000].strip()
            if len(chunk) < 40:
                continue

            ids.append(f"page{pdf_page}_chunk{start}")
            documents.append(chunk)
            metadata.append({
                "subject": subject,
                "chapter": chapter,
                "page": pdf_page,
                "textbook_page": pdf_page - 8,
                "source": PDF_PATH.name,
            })

    pdf.close()

    if not documents:
        raise ValueError("No readable textbook text was found.")

    embeddings = get_model().encode(
        documents, normalize_embeddings=True
    ).tolist()

    collection.upsert(
        ids=ids,
        documents=documents,
        metadatas=metadata,
        embeddings=embeddings,
    )

    return {
        "subject": subject,
        "pages": 360,
        "chunks_indexed": len(documents),
        "chapters": len(CHAPTERS),
    }


def retrieve_text(question, subject="Science", limit=4, lesson=None):
    collection = get_collection(subject)

    options = {
        "query_embeddings": get_model().encode(
            [question], normalize_embeddings=True
        ).tolist(),
        "n_results": limit,
        "include": ["documents", "metadatas"],
    }

    if lesson:
        valid_chapters = {name for name, _ in CHAPTERS}
        if lesson not in valid_chapters:
            raise ValueError(f"Unknown Science chapter: {lesson}")
        options["where"] = {"chapter": lesson}

    results = collection.query(**options)
    sources = []

    for doc, meta in zip(
        results["documents"][0], results["metadatas"][0]
    ):
        sources.append({
            "text": doc,
            "page": meta["page"],
            "textbook_page": meta["textbook_page"],
            "chapter": meta["chapter"],
            "source": meta["source"],
        })

    return sources
