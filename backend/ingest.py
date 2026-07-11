import os

try:
    from backend.database import VectorDB
except ModuleNotFoundError:  # pragma: no cover - direct script execution fallback
    from database import VectorDB

from langchain_text_splitters import RecursiveCharacterTextSplitter

# Initializing components
db = VectorDB()
collection = db.get_or_create_collection()

# Data paths
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

LOCATION_FILES = {
    "mather_point.txt": "mather_point",
    "indian_garden.txt": "indian_garden",
    "colorado_river.txt": "colorado_river"
}

def ingest_data():
    if collection is None:
        raise RuntimeError("Vector collection could not be initialized. Check chromadb and embeddings setup.")

    # Initializing Langchain text splitter
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        separators=["\n\n", "\n", ".", " "]
    )
    total_chunks = 0

    for filename, room_tag in LOCATION_FILES.items():
        file_path = os.path.join(DATA_DIR, filename)

        if not os.path.exists(file_path):
            print(f"Skipping {filename}: File not found in {DATA_DIR}.")
            continue

        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()

            # Using langchain to smartly chunk the text
            chunks = text_splitter.split_text(content)

            for i, chunk_text in enumerate(chunks):
                # Generating Unique ID for each chunks
                doc_id = f"{room_tag}_chunk_{i}"

                # Inserting ChromaDB with metadata tagging for Strict Isolation
                collection.upsert(
                    documents=[chunk_text],
                    metadatas=[{"room": room_tag}],
                    ids=[doc_id]
                )
            total_chunks += len(chunks)
            print(f"Ingested {filename} into {len(chunks)} chunks and tagged with room: '{room_tag}'")

    print(f"\nTotal documents ingested: {total_chunks}")


if __name__ == "__main__":
    ingest_data()
    print(f"\n Total Documents in DB: {collection.count()}")