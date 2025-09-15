# intent_firewall.py
import datetime
import pytz
import re
from smart_home_api import control_device

LOCAL_TZ = pytz.timezone("Asia/Kolkata")

# ---------- Formatting Helpers ----------
def format_blocked_response(reason, suggestion="Action cancelled for safety."):
    return f"""🚫 Command Blocked by Intent Firewall
Reason: {reason}
Suggestion: {suggestion}"""

def format_confirmation_response(reason):
    return f"""⚠️ Confirmation Required
Reason: {reason}
Are you sure you want to continue? (yes/no)"""

# ---------- Firewall ----------
def intent_firewall(command, system_state=None, raw_text=""):
    """
    Unified firewall with safety rules for all smart home devices.
    Returns (allowed: bool, message: str, requires_confirmation: bool)
    """
    now = datetime.datetime.now(LOCAL_TZ)

    device = command.get("device", "").lower()
    location = command.get("location", "").lower()
    action = command.get("action", "").lower()
    text_check = raw_text.lower()

    # ====== ALWAYS SAFE INTENTS ======
    if action in ["status", "get_status", "list_devices"]:
        return (True, "", False)

    # Normalize synonyms
    if action in ["check", "show"]:
        action = "status"

    # ====== LIGHTING SAFETY RULES ======
    if "light" in device or device in ["lamp", "chandelier", "led strip", "bulb"]:
        if action == "turn_off":
            if "all" in location or "all lights" in text_check:
                if now.hour >= 22 or now.hour < 6:
                    return (False, format_confirmation_response(
                        "Turning off all lights after 10PM may cause unsafe conditions."
                    ), True)

            if "kids" in location and system_state and system_state.get("kids_room_occupied"):
                return (False, format_blocked_response(
                    "Cannot turn off lights in the kids' room while occupied.",
                    "Leave lights on or wait until room is empty."
                ), False)

            if "stair" in location and (now.hour >= 22 or now.hour < 6):
                return (False, format_confirmation_response(
                    "Stair lights should remain on at night for safety."
                ), True)

        if action == "set_brightness":
            brightness = re.findall(r"\b(\d+)%?\b", text_check)
            if brightness and int(brightness[0]) > 90 and (now.hour >= 22 or now.hour < 6):
                return (False, format_confirmation_response(
                    "Brightness above 90% at night may disturb sleep."
                ), True)

    # ====== DOOR & SECURITY ======
    if device in ["door", "lock", "smart lock"]:
        if action in ["unlock", "open"]:
            if "all doors" in text_check:
                return (False, format_blocked_response(
                    "Unlocking all doors is unsafe.",
                    "Unlock doors individually only."
                ), False)
            if now.hour >= 23 or now.hour < 6:
                return (False, format_confirmation_response(
                    "Unlocking doors between 11PM–6AM may be unsafe."
                ), True)
            if "stranger" in text_check:
                return (False, format_blocked_response(
                    "Cannot unlock the door for unknown persons.",
                    "Allow only verified household members."
                ), False)

    # ====== KITCHEN APPLIANCES ======
    kitchen = ["oven", "stove", "microwave", "pressure cooker", "blender", "food processor"]
    if device in kitchen and action in ["turn_on", "start", "preheat"]:
        if now.hour >= 23 or now.hour < 6:
            return (False, format_confirmation_response(
                f"Using {device} at night may be unsafe."
            ), True)

        if device == "oven":
            temps = re.findall(r"\b(\d{3})\b", text_check)
            if temps and int(temps[0]) > 250:
                return (False, format_confirmation_response(
                    "High oven temperature above 250°C detected."
                ), True)

    # ====== CLIMATE CONTROL ======
    climate = ["thermostat", "air conditioning", "heater", "humidifier", "dehumidifier"]
    if device in climate:
        temps = re.findall(r"\b(\d{1,2})\b", text_check)
        if temps:
            t = int(temps[0])
            if device in ["thermostat", "air conditioning", "heater"]:
                if t < 10 or t > 32:
                    return (False, format_blocked_response(
                        "Temperature must stay between 10–32°C.",
                        "Choose a safer range."
                    ), False)
            if device == "humidifier":
                hum = re.findall(r"\b(\d{2,3})%?\b", text_check)
                if hum and int(hum[0]) > 80:
                    return (False, format_confirmation_response(
                        "Humidity above 80% may cause mold."
                    ), True)

    # ====== BATHROOM APPLIANCES ======
    if device == "water heater" and action in ["turn_on", "set_temperature"]:
        temps = re.findall(r"\b(\d{1,3})\b", text_check)
        if temps and int(temps[0]) > 60:
            return (False, format_blocked_response(
                "Water temperature above 60°C may cause burns.",
                "Keep water heater below 60°C."
            ), False)

    # ====== SECURITY CAMERAS ======
    if device in ["security camera", "camera"] and action in ["turn_off", "disable"]:
        if now.hour >= 22 or now.hour < 8:
            return (False, format_blocked_response(
                "Disabling cameras at night compromises security.",
                "Keep cameras enabled overnight."
            ), False)

    # ====== OUTDOOR ======
    outdoor = ["pool pump", "pool heater", "hot tub", "sprinkler system", "outdoor grill"]
    if device in outdoor and action == "turn_on":
        if device in ["pool pump", "hot tub"] and (now.hour >= 22 or now.hour < 7):
            return (False, format_confirmation_response(
                f"Operating {device} at night may disturb neighbors."
            ), True)
        if device == "hot tub":
            temps = re.findall(r"\b(\d{2})\b", text_check)
            if temps and int(temps[0]) > 40:
                return (False, format_blocked_response(
                    "Hot tub temperature above 40°C is unsafe.",
                    "Keep water temp below 40°C."
                ), False)

    # ====== ROBOTS / LAUNDRY ======
    if device in ["robot vacuum", "robot lawn mower", "washing machine", "dryer"] and action in ["start", "turn_on"]:
        if now.hour >= 22 or now.hour < 7:
            return (False, format_confirmation_response(
                f"Running {device} during quiet hours may disturb others."
            ), True)

    # ====== MEDICINE CABINET ======
    if device == "medicine cabinet" and action == "open":
        if system_state and system_state.get("child_lock_enabled"):
            return (False, format_confirmation_response(
                "Medicine cabinet is locked. Adult supervision required."
            ), True)

    # ====== UNSAFE PHRASES ======
    unsafe = [
        "disable all security", "turn off all alarms", "disable smoke detector",
        "unlock all doors", "stop all security cameras", "disable child lock"
    ]
    if any(p in text_check for p in unsafe):
        return (False, format_blocked_response(
            "Command violates core safety rules.",
            "Manual override is not allowed."
        ), False)

    return (True, "", False)
