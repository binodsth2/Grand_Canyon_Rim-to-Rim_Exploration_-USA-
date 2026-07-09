import os
from langchain_text_splitters import RecursiveCharacterTextSplitter
from backend.database import VectorDB

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
    # Initializing Langchain text splitter
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        separators=["\n\n", "\n", ".", " "]
    )
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
    print(f"Ingested {filename} into {len(chunks)} chunks and tagged with room: '{room_tag}'")


if __name__ == "__main__":
    ingest_data()
    print(f"\n Total Documents in DB: {collection.count()}")