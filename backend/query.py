from backend.database import VectorDB

# Connect to the database
db = VectorDB()
collection = db.get_or_create_collection()

GRAPH = {
    "mather_point": ["indian_garden"],
    "indian_garden": ["mather_point", "colorado_river"],
    "colorado_river": ["indian_garden"],
}


def search_location(question, current_room):
    print(f"\n📍 Agent is currently in room: {current_room}")
    print(f"❓ Question: '{question}'")

    results = collection.query(
        query_texts=[question],
        n_results=2,
        where={"room": current_room}
    )

    if results['documents'] and len(results['documents'][0]) > 0:
        for i, doc in enumerate(results['documents'][0]):
            print(f"   -> Result {i+1}: {doc[:100]}...")
    else:
        print("   -> No relevant information found in this location.")


def look_up_artifact(item, current_room):
    results = collection.query(
        query_texts=[item],
        n_results=1,
        where={"room": current_room}
    )

    if results.get("documents") and results["documents"] and results["documents"][0]:
        return results["documents"][0][0]
    return None


def change_location(session, target_room):
    current_room = session["current_room"]

    if target_room not in GRAPH:
        raise ValueError("Unknown target room")

    if target_room not in GRAPH[current_room]:
        raise ValueError(f"Cannot move from {current_room} to {target_room}")

    if target_room == "colorado_river" and "electrolyte_packets" not in session.get("inventory", []):
        raise ValueError("Electrolyte Packets are required to move to the Colorado River")

    session["current_room"] = target_room
    return session["current_room"]


def calculate_heat_risk(temperature, elevation_drop):
    if temperature >= 95 and elevation_drop >= 1500:
        return "critical"
    if temperature >= 85 and elevation_drop >= 1000:
        return "high"
    if temperature >= 75:
        return "moderate"
    return "low"


if __name__ == "__main__":
    test_question = "Tell me about the river and its elevation."

    search_location(test_question, current_room="mather_point")
    search_location(test_question, current_room="colorado_river")
