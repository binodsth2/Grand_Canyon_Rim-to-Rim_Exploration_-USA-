import chromadb
from chromadb.utils import embedding_functions
import os

#  Database path where chromaDB will store data locally
DB_PATH = os.path.join(os.path.dirname(__file__), ".chroma_db")

class VectorDB:
    def __init__(self):
        self.client = chromadb.PersistentClient(path=DB_PATH)

        # I use the default sentence-transformer embedding function
        # This model converts text into vector numbers
        self.embedding_fn = embedding_functions.DefaultEmbeddingFunction()

        print(f"ChromDB directory: {DB_PATH}")

    def get_or_create_collection(self, collection_name="grand_canyon_locations"):
        """
        Getting existing collection or creates a new one one if doesnot exist
        Collection like table in a standard SQL database
        """
        collection = self.client.get_or_create_collection(
            name = collection_name,
            embedding_function = self.embedding_fn
        )
        return collection

#   Testing the initialization if this script is run directly
if __name__ == '__main__':
    db = VectorDB()
    collection = db.get_or_create_collection()
    print(f"Collection '{collection.name}' is ready. \n Current document count: {collection.count()}")