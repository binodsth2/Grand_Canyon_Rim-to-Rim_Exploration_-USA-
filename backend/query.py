from backend.database import VectorDB

# Connect to the database
try:
    db = VectorDB()
    collection = db.get_or_create_collection()
except Exception:  # pragma: no cover - fallback when vector DB dependencies are unavailable
    db = None
    collection = None

GRAPH = {
    "mather_point": ["indian_garden"],
    "indian_garden": ["mather_point", "colorado_river"],
    "colorado_river": ["indian_garden"],
}


def search_location(question, current_room):
    print(f"\n📍 Agent is currently in room: {current_room}")
    print(f"❓ Question: '{question}'")

    if collection is None:
        print("   -> Vector storage is unavailable in this environment.")
        return

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
    if not item or not current_room or collection is None:
        return None

    results = collection.query(
        query_texts=[item],
        n_results=1,
        where={"room": current_room}
    )

    documents = results.get("documents") or []
    if documents and documents[0]:
        return documents[0][0]
    return None


def change_location(session, target_room):
    if not isinstance(session, dict):
        raise ValueError("Session must be a dictionary")

    current_room = session.get("current_room")
    if not current_room:
        raise ValueError("Current room is not set")

    if target_room not in GRAPH:
        raise ValueError("Unknown target room")

    if target_room not in GRAPH[current_room]:
        raise ValueError(f"Cannot move from {current_room} to {target_room}")

    inventory = session.get("inventory", [])
    normalized_inventory = {
        str(item).strip().lower().replace(" ", "_")
        for item in inventory
    }

    if target_room == "colorado_river" and "electrolyte_packets" not in normalized_inventory:
        raise ValueError("Electrolyte Packets are required to move to the Colorado River")

    session["current_room"] = target_room
    return session["current_room"]


def calculate_heat_risk(temperature, elevation_drop):
    try:
        temp_value = float(temperature)
        drop_value = float(elevation_drop)
    except (TypeError, ValueError):
        return "low"

    if temp_value >= 95 and drop_value >= 1500:
        return "critical"
    if temp_value >= 85 and drop_value >= 1000:
        return "high"
    if temp_value >= 75:
        return "moderate"
    return "low"


if __name__ == "__main__":
    test_question = "Tell me about the river and its elevation."

    search_location(test_question, current_room="mather_point")
    search_location(test_question, current_room="colorado_river")
