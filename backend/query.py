from backend.database import VectorDB

# Connect to the database
db = VectorDB()
collection = db.get_or_create_collection()

def search_location(question, current_room):
    print(f"\n📍 Agent is currently in room: {current_room}")
    print(f"❓ Question: '{question}'")
    
    # This is where STRICT ISOLATION happens!
    # The `where` clause forces the database to only return documents tagged with the current_room
    results = collection.query(
        query_texts=[question],
        n_results=2,
        where={"room": current_room} # <-- The isolation filter
    )
    
    # Check if we got results
    if results['documents'] and len(results['documents'][0]) > 0:
        for i, doc in enumerate(results['documents'][0]):
            print(f"   -> Result {i+1}: {doc[:100]}...") # Print first 100 characters
    else:
        print("   -> No relevant information found in this location.")

if __name__ == "__main__":
    test_question = "Tell me about the river and its elevation."
    
    # Test 1: The agent is at Mather Point. It should NOT know about the river's details yet.
    search_location(test_question, current_room="mather_point")
    
    # Test 2: The agent arrives at the Colorado River. Now it CAN access the river's details.
    search_location(test_question, current_room="colorado_river")
