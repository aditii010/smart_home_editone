import json
import os
import datetime


class StateManager:
    def __init__(self, context_file=None):
        """
        Loads initial context (summary of dataset) and sets up state tracking.
        context_file: path to data/context_summary.json
        """
        self.state = {}
        self.context = {}

        if context_file and os.path.exists(context_file):
            try:
                with open(context_file, "r") as f:
                    self.context = json.load(f)
            except json.JSONDecodeError:
                print(f"[WARNING] Could not parse {context_file}, starting with empty context.")
        else:
            print(f"[INFO] No context file found at {context_file}, starting with empty context.")

        # Pre-populate state from context summary if available
        self._init_state_from_context()

    def _init_state_from_context(self):
        """
        Initialize state variables from the loaded context summary.
        This is optional and depends on what’s in your dataset summary.
        """
        for device_info in self.context.get("devices", []):
            key = f"{device_info.get('device')}_{device_info.get('location')}"
            self.state[key] = device_info.get("status", "unknown")

    def get_state(self):
        """Return the current system state dictionary."""
        return self.state

    def update_state(self, device, location, action):
        """
        Update the in-memory system state based on device, location, and action.
        """
        device = device.lower().strip()
        location = location.lower().strip()
        key = f"{device}_{location}"

        # Handle device-specific updates
        if device == "light":
            if action in ["turn_on", "on"]:
                self.state[key] = "on"
            elif action in ["turn_off", "off"]:
                self.state[key] = "off"

        elif device == "door":
            if action in ["lock"]:
                self.state[key] = "locked"
            elif action in ["unlock", "open"]:
                self.state[key] = "unlocked"

        elif device == "thermostat":
            # Example: action could be "set_22" meaning set to 22°C
            if action.startswith("set_"):
                try:
                    temp = int(action.split("_")[1])
                    self.state[key] = f"{temp}°C"
                except (ValueError, IndexError):
                    self.state[key] = "unknown"

        else:
            # Default generic assignment
            self.state[key] = action

    def is_kids_room_occupied(self):
        """Example helper for firewall checks."""
        return self.state.get("light_kids_room") == "on"

    def is_door_unlocked_at_night(self):
        """Example helper to detect unsafe door state after 10PM."""
        now = datetime.datetime.now()
        for k, v in self.state.items():
            if k.startswith("door_") and v == "unlocked" and now.hour >= 22:
                return True
        return False
