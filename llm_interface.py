# llm_interface.py - FIXED VERSION

import subprocess
import json
import re
import sys
import os
from smart_home_api import control_device

# -------------------
# Command Normalization
# -------------------
def normalize_command(cmd):
    """Normalize command dictionary"""
    if isinstance(cmd, dict):
        device = cmd.get("device", "").lower().strip()
        location = cmd.get("location", "").lower().strip()
        action = cmd.get("action", "").lower().strip()

        # Normalize device names
        device_mapping = {
            "lights": "light", "lamp": "light", "bulb": "light",
            "thermostat": "thermostat", "temp": "thermostat",
            "door": "door", "lock": "door",
            "humidifier": "humidifier", "heater": "heater",
            "oven": "smart_oven", "microwave": "microwave"
        }
        device = device_mapping.get(device, device)

        # Normalize locations - map unknown/empty to "all"
        location_mapping = {
            "all": "all", "everywhere": "all", "": "all", "unknown": "all",
            "bedroom": "bedroom", "kitchen": "kitchen",
            "living room": "living room", "bathroom": "bathroom"
        }
        location = location_mapping.get(location, "all")

        return {
            "device": device,
            "location": location,
            "action": action
        }
    return cmd

# -------------------
# Parse LLM Output
# -------------------
def safe_parse_multiple_json(raw_output):
    """Parse LLM output safely"""
    if not raw_output:
        return None

    # Ensure Unicode errors don't crash us
    if isinstance(raw_output, bytes):
        raw_output = raw_output.decode("utf-8", errors="ignore")

    print(f"[DEBUG] Parsing raw output: {repr(raw_output)}")

    try:
        parsed = json.loads(raw_output)
        if isinstance(parsed, dict):
            return [normalize_command(parsed)]
        elif isinstance(parsed, list):
            return [normalize_command(item) for item in parsed if isinstance(item, dict)]
    except json.JSONDecodeError:
        # Try to extract JSON using regex
        json_match = re.search(r'\{[^{}]*\}', raw_output)
        if json_match:
            try:
                parsed = json.loads(json_match.group())
                return [normalize_command(parsed)]
            except json.JSONDecodeError:
                pass

    print("[DEBUG] Parsing failed")
    return None

# -------------------
# Query LLM / Fallback
# -------------------
def query_llm(user_input):
    """Main LLM query function with quick fallback"""
    print(f"[LLM] Processing: {user_input}")

    input_lower = user_input.lower().strip()

    # -------- Quick Local Fallbacks --------
    fallback_mapping = {
        "thermostat": ["turn_on", "turn_off", "get_status"],
        "light": ["turn_on", "turn_off"],
        "humidifier": ["turn_on", "turn_off", "set_level"],
        "heater": ["turn_on", "turn_off"],
        "smart_oven": ["turn_on", "turn_off", "preheat"],
        "microwave": ["turn_on", "turn_off"],
        "security_camera": ["turn_on", "turn_off"]
    }

    for device, actions in fallback_mapping.items():
        if device in input_lower:
            action = None
            for a in actions:
                if a.replace("_", " ") in input_lower:
                    action = a
                    break
            if not action:
                # Default action
                action = actions[0]
            print(f"[LLM] Quick fallback result: device={device}, action={action}")
            return [{"device": device, "location": "all", "action": action}]

    # -------- Call Ollama Subprocess --------
    try:
        print("[LLM] Attempting Ollama call...")
        result = subprocess.run(
            ["ollama", "run", "mistral"],
            input=f'Convert to JSON: "{user_input}" -> {{"device": "", "location": "all", "action": ""}}',
            capture_output=True,
            text=True,                # forces str output
            encoding="utf-8",         # explicitly use UTF-8
            errors="ignore",          # ignore decode errors
            timeout=5
        )

        if result.returncode == 0 and result.stdout.strip():
            output = result.stdout.strip()
            print(f"[LLM] Ollama output: {output[:200]}...")
            parsed_commands = safe_parse_multiple_json(output)
            if parsed_commands:
                print(f"[LLM] Successfully parsed: {parsed_commands}")
                return parsed_commands

    except subprocess.TimeoutExpired:
        print("[LLM] Ollama timed out, using fallback")
    except Exception as e:
        print(f"[LLM] Ollama error: {e}, using fallback")

    # -------- Final Fallback --------
    print("[LLM] No command recognized")
    return None
