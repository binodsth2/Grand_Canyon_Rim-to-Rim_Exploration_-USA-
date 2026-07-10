import unittest
from unittest.mock import patch

from backend.agent import AgentService


class AgentIntegrationTests(unittest.TestCase):
    def test_agent_uses_current_room_context(self):
        session = {"current_room": "mather_point", "inventory": [], "discovered_clues": []}
        agent = AgentService()

        with patch("backend.agent.look_up_artifact", return_value="Mather Point overlook details") as mocked_lookup:
            response = agent.respond("Tell me about this place", session)

        self.assertIn("Mather Point", response)
        mocked_lookup.assert_called_once()

    def test_agent_reports_move_blockers(self):
        session = {"current_room": "indian_garden", "inventory": [], "discovered_clues": []}
        agent = AgentService()

        with patch("backend.agent.change_location", side_effect=ValueError("Electrolyte Packets are required")):
            response = agent.respond("Take me to the Colorado River", session)

        self.assertIn("Electrolyte", response)


if __name__ == "__main__":
    unittest.main()
