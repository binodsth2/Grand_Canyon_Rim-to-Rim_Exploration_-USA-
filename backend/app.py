from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uuid
from typing import Dict, List
from backend.query import search_location

sessions: Dict[str, Dict] = {}

#  Directed graph adjacency for Bright Angel Trail
GRAPH = {
    "mather_point": ["indian_garden"],
    "indian_garden": ["mather_point", "colorado_river"],
    "colorado_river": ["indian_garden"]
}

app = FastAPI(title="Grand Canyon Spatial State Machine")

class CreateSessionResponse(BaseModel):
    session_id: str
    current_room: str
    inventory: List[str]

class MoveRequest(BaseModel):
    to: str

class PickupRequest(BaseModel):
    item: str

class queryRequest(BaseModel):
    session_id: str
    question: str

@app.post("/session", response_model=CreateSessionResponse)
def create_session():
    session_id = str(uuid.uuid4())
    sessions[session_id] = {
        "current_room": "mather_point",
        "inventory": [],
        "discovered_clues": []
    }
    return {"session_id": session_id, "current_room": "mather_point", "inventory": []}

@app.get("/session/{session_id}")
def get_session(session_id: str):
    session = sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session

@app.post("/session/{session_id}/move")
def move(session_id: str, req: MoveRequest):
    session = sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    current = session["current_room"]
    target = req.to

    if target not in GRAPH:
        raise HTTPException(status_code=400, detail="Unknown target room")

    if target not in GRAPH[current]:
        raise HTTPException(status_code=400, detail=f"Cannot move from {current} to {target}")

    if target == "colorado_river" and "electrolyte_packets" not in session["inventory"]:
        raise HTTPException(status_code=403, detail="Electrolyte Packets are required to move to the Colorado River")

    session["current_room"] = target
    return {"session_id": session_id, "current_room": target, "inventory": session["inventory"]}


@app.post("/session/{session_id}/pickup")
def pickup(session_id: str, req: PickupRequest):
    session = sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    item = req.item
    if item not in session["inventory"]:
        session["inventory"].append(item)
    return {"session_id": session_id, "inventory": session["inventory"]}

@app.post("/query/")
def query_location(req: queryRequest):
    session = sessions.get(req.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    current_room = session["current_room"]
    return search_location(req.question, current_room)
