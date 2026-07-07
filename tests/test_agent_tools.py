import unittest
from unittest.mock import Mock, patch

from backend import query


class AgentToolsTests(unittest.TestCase):
    def test_look_up_artifact_filters_by_room(self):
        fake_collection = Mock()
        fake_collection.query.return_value = {"documents": [["River context"]]} 

        with patch.object(query, "collection", fake_collection):
            result = query.look_up_artifact("river", "colorado_river")

        self.assertEqual(result, "River context")
        fake_collection.query.assert_called_once_with(
            query_texts=["river"],
            n_results=1,
            where={"room": "colorado_river"},
        )

    def test_change_location_requires_item_for_river(self):
        session = {"current_room": "indian_garden", "inventory": []}
        with self.assertRaises(ValueError):
            query.change_location(session, "colorado_river")

        session = {"current_room": "indian_garden", "inventory": ["electrolyte_packets"]}
        self.assertEqual(query.change_location(session, "colorado_river"), "colorado_river")

    def test_calculate_heat_risk_levels(self):
        self.assertEqual(query.calculate_heat_risk(70, 500), "low")
        self.assertEqual(query.calculate_heat_risk(85, 1100), "high")
        self.assertEqual(query.calculate_heat_risk(95, 1800), "critical")


if __name__ == "__main__":
    unittest.main()
