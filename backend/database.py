import hashlib
import os

try:
    import chromadb
    from chromadb.utils import embedding_functions
except ImportError:  # pragma: no cover - optional dependency in test environment
    chromadb = None
    embedding_functions = None

#  Database path where chromaDB will store data locally
DB_PATH = os.path.join(os.path.dirname(__file__), ".chroma_db")


class DeterministicEmbeddingFunction:
    """Offline embedding fallback used to keep the vector store self-contained."""

    def __init__(self, dimension=384):
        self.dimension = dimension

    def name(self):
        return "default"

    def __call__(self, input):
        if isinstance(input, str):
            input = [input]

        vectors = []
        for text in input:
            tokens = [token for token in str(text).lower().split() if token]
            vector = [0.0] * self.dimension

            if not tokens:
                vectors.append(vector)
                continue

            for index, token in enumerate(tokens[: self.dimension]):
                digest = int(hashlib.sha256(token.encode("utf-8")).hexdigest(), 16)
                vector[index] = (digest % 1000) / 1000.0

            average_scale = max(1, len(tokens))
            for idx in range(self.dimension):
                vector[idx] = round(vector[idx] / average_scale, 6)

            vectors.append(vector)

        return vectors


class VectorDB:
    def __init__(self):
        self.client = None
        self.embedding_fn = DeterministicEmbeddingFunction()

        if chromadb is None:
            return

        self.client = chromadb.PersistentClient(path=DB_PATH)
        print(f"ChromDB directory: {DB_PATH}")

    def get_or_create_collection(self, collection_name="grand_canyon_locations"):
        """
        Getting existing collection or creates a new one one if doesnot exist
        Collection like table in a standard SQL database
        """
        if self.client is None or self.embedding_fn is None:
            return None

        collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=self.embedding_fn,
        )
        return collection

#   Testing the initialization if this script is run directly
if __name__ == '__main__':
    db = VectorDB()
    collection = db.get_or_create_collection()
    print(f"Collection '{collection.name}' is ready. \n Current document count: {collection.count()}")