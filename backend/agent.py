import os
from typing import Any, Dict

from backend.query import calculate_heat_risk, change_location, look_up_artifact


class AgentService:
    def __init__(self):
        self.system_prompt = (
            "You are a Grand Canyon trail guide. "
            "Use only information relevant to the user's current room. "
            "Do not reveal details from other locations unless the user has reached them. "
            "If the user asks about movement, use the movement tool and explain any blockers."
        )

    def respond(self, user_message: str, session: Dict[str, Any]) -> str:
        if not user_message:
            return "I can help guide you along the trail."

        current_room = session.get("current_room", "mather_point")
        inventory = session.get("inventory", [])
        discovered_clues = session.get("discovered_clues", [])

        if "move" in user_message.lower() or "go to" in user_message.lower() or "take me" in user_message.lower():
            target_room = None
            lowered = user_message.lower()
            if "colorado river" in lowered:
                target_room = "colorado_river"
            elif "indian garden" in lowered:
                target_room = "indian_garden"
            elif "mather point" in lowered:
                target_room = "mather_point"

            if target_room:
                try:
                    new_room = change_location(session, target_room)
                    return f"You moved to {new_room}."
                except ValueError as exc:
                    return str(exc)

        if "heat" in user_message.lower() or "risk" in user_message.lower():
            return f"Heat risk is {calculate_heat_risk(85, 1200)}."

        artifact = look_up_artifact(user_message, current_room)
        if artifact:
            return f"In {current_room.replace('_', ' ')}: {artifact}"

        return (
            f"I can guide you from {current_room.replace('_', ' ')}. "
            f"You currently carry: {', '.join(inventory) if inventory else 'nothing'}."
        )
