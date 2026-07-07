from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uuid
from typing import Dict, List
from backend.query import search_location, look_up_artifact, change_location, calculate_heat_risk

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

    try:
        target = change_location(session, req.to)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

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
    artifact = look_up_artifact(req.question, current_room)
    if artifact:
        return {"answer": artifact, "current_room": current_room}
    return {"answer": "No relevant information found in this location.", "current_room": current_room}


@app.get("/session/{session_id}/heat-risk")
def heat_risk(session_id: str):
    session = sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    temperature = 85
    elevation_drop = 1200
    return {
        "session_id": session_id,
        "current_room": session["current_room"],
        "heat_risk": calculate_heat_risk(temperature, elevation_drop),
        "temperature": temperature,
        "elevation_drop": elevation_drop,
    }
