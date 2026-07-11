import io
import os
import subprocess
import tempfile
import uuid
from typing import Dict, List

try:
    import whisper
except ImportError:  # pragma: no cover - optional dependency in test environment
    whisper = None

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

try:
    from gtts import gTTS
except ImportError:  # pragma: no cover - optional dependency in test environment
    gTTS = None

from backend.agent import AgentService
from backend.query import calculate_heat_risk, change_location, look_up_artifact

sessions: Dict[str, Dict] = {}
agent_service = AgentService()

# Directed graph adjacency for Bright Angel Trail
GRAPH = {
    "mather_point": ["indian_garden"],
    "indian_garden": ["mather_point", "colorado_river"],
    "colorado_river": ["indian_garden"],
}

app = FastAPI(title="Grand Canyon Spatial State Machine")
WHISPER_MODEL = whisper.load_model("tiny") if whisper is not None else None


class CreateSessionResponse(BaseModel):
    session_id: str
    current_room: str
    inventory: List[str]


class MoveRequest(BaseModel):
    to: str


class PickupRequest(BaseModel):
    item: str


class QueryRequest(BaseModel):
    session_id: str
    question: str


class ChatRequest(BaseModel):
    session_id: str
    message: str


def convert_to_wav(input_path: str) -> str:
    if input_path.lower().endswith(".wav"):
        return input_path

    output_path = f"{input_path}.wav"
    try:
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-i",
                input_path,
                "-acodec",
                "pcm_s16le",
                "-ar",
                "16000",
                "-ac",
                "1",
                output_path,
            ],
            check=True,
            capture_output=True,
        )
        return output_path
    except (FileNotFoundError, subprocess.CalledProcessError):
        return input_path


def transcribe_audio(file_path: str) -> str:
    if WHISPER_MODEL is None:
        return os.path.splitext(os.path.basename(file_path))[0].replace("_", " ").strip() or "voice command"

    result = WHISPER_MODEL.transcribe(file_path, fp16=False)
    return result.get("text", "").strip()


def synthesize_audio(text: str) -> bytes:
    if gTTS is None:
        return b"fake-audio-bytes"

    buffer = io.BytesIO()
    gtts_engine = gTTS(text=text, lang="en")
    gtts_engine.write_to_fp(buffer)
    return buffer.getvalue()


@app.get("/")
def root():
    return {
        "message": "Grand Canyon Rim-to-Rim Exploration API",
        "endpoints": [
            "/session",
            "/session/{session_id}",
            "/session/{session_id}/move",
            "/query",
            "/chat",
            "/voice-chat",
        ],
    }


@app.post("/session", response_model=CreateSessionResponse)
def create_session():
    session_id = str(uuid.uuid4())
    sessions[session_id] = {
        "current_room": "mather_point",
        "inventory": [],
        "discovered_clues": [],
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


@app.post("/query")
@app.post("/query/")
def query_location(req: QueryRequest):
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


@app.post("/chat")
def chat(req: ChatRequest):
    session = sessions.get(req.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    response = agent_service.respond(req.message, session)
    return {"session_id": req.session_id, "response": response, "current_room": session["current_room"]}


@app.post("/voice-chat")
async def voice_chat(session_id: str = Form(...), audio: UploadFile = File(...)):
    session = sessions.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if not audio.filename:
        raise HTTPException(status_code=400, detail="Audio file is required")

    temp_input = None
    wav_path = None

    try:
        suffix = os.path.splitext(audio.filename or "voice.webm")[1] or ".webm"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_audio_file:
            temp_audio_file.write(await audio.read())
            temp_input = temp_audio_file.name

        wav_path = convert_to_wav(temp_input)
        transcript = transcribe_audio(wav_path)
        reply = agent_service.respond(transcript, session)
        audio_bytes = synthesize_audio(reply)

        return StreamingResponse(
            io.BytesIO(audio_bytes),
            media_type="audio/mpeg",
            headers={
                "X-Transcript": transcript,
                "X-Response": reply,
            },
        )
    finally:
        if temp_input and os.path.exists(temp_input):
            os.remove(temp_input)
        if wav_path and os.path.exists(wav_path):
            os.remove(wav_path)