import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.app import app


class AppRoutesTests(unittest.TestCase):
    def test_root_endpoint_returns_info(self):
        client = TestClient(app)
        response = client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Grand Canyon", response.text)

    def test_voice_chat_returns_audio_and_transcript(self):
        client = TestClient(app)
        session_response = client.post("/session")
        session_id = session_response.json()["session_id"]

        with patch("backend.app.convert_to_wav", return_value="voice.wav"), \
             patch("backend.app.transcribe_audio", return_value="take me to the colorado river"), \
             patch("backend.app.synthesize_audio", return_value=b"fake-audio-bytes"):
            response = client.post(
                "/voice-chat",
                files={"audio": ("voice.webm", b"fake-audio-bytes", "audio/webm")},
                data={"session_id": session_id},
            )

        self.assertEqual(response.status_code, 200)
        self.assertIn("audio/mpeg", response.headers["content-type"])
        self.assertEqual(response.headers["x-transcript"], "take me to the colorado river")


if __name__ == "__main__":
    unittest.main()
