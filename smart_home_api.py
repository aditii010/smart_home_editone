# =========================
# smart_home_api.py (70 devices + XAI explanations)
# =========================

device_states = {
    # Climate Control
    "smart_thermostat": {"status": "off", "temperature": 22},
    "air_conditioner": {"status": "off", "temperature": 24},
    "heater": {"status": "off", "temperature": 20},
    "humidifier": {"status": "off", "humidity": 45},
    "dehumidifier": {"status": "off", "humidity": 55},
    "air_purifier": {"status": "off", "mode": "auto"},

    # Lighting
    "bedroom_light": {"status": "off", "brightness": 100},
    "kitchen_light": {"status": "off", "brightness": 100},
    "living_room_light": {"status": "off", "brightness": 100},
    "bathroom_light": {"status": "off", "brightness": 100},
    "garden_light": {"status": "off", "brightness": 100},
    "stair_light": {"status": "off", "brightness": 100},
    "garage_light": {"status": "off", "brightness": 100},
    "chandelier": {"status": "off", "brightness": 80},
    "led_strip": {"status": "off", "color": "white"},

    # Security
    "front_door": {"status": "locked"},
    "back_door": {"status": "locked"},
    "garage_door": {"status": "closed"},
    "balcony_door": {"status": "locked"},
    "security_camera": {"status": "off"},
    "doorbell_camera": {"status": "off"},
    "window_sensor": {"status": "armed"},
    "alarm_system": {"status": "armed"},
    "motion_detector": {"status": "armed"},

    # Kitchen
    "smart_oven": {"status": "off"},
    "stove": {"status": "off"},
    "microwave": {"status": "off"},
    "toaster": {"status": "off"},
    "coffee_machine": {"status": "off"},
    "blender": {"status": "off"},
    "food_processor": {"status": "off"},
    "dishwasher": {"status": "off"},
    "fridge": {"status": "on", "temperature": 4},
    "freezer": {"status": "on", "temperature": -18},
    "pressure_cooker": {"status": "off"},

    # Entertainment
    "smart_tv": {"status": "off", "volume": 20},
    "gaming_console": {"status": "off"},
    "projector": {"status": "off"},
    "smart_speaker": {"status": "off", "volume": 50},
    "home_theater": {"status": "off", "volume": 30},

    # Cleaning & Laundry
    "robot_vacuum": {"status": "docked"},
    "robot_lawn_mower": {"status": "docked"},
    "washing_machine": {"status": "off"},
    "dryer": {"status": "off"},
    "steam_iron": {"status": "off"},

    # Bathroom
    "water_heater": {"status": "off", "temperature": 45},
    "smart_shower": {"status": "off", "temperature": 37},
    "bath_exhaust_fan": {"status": "off"},
    "toothbrush_sanitizer": {"status": "off"},

    # Outdoor
    "pool_pump": {"status": "off"},
    "pool_heater": {"status": "off", "temperature": 28},
    "hot_tub": {"status": "off", "temperature": 38},
    "sprinkler_system": {"status": "off"},
    "outdoor_grill": {"status": "off"},
    "garden_irrigation": {"status": "off"},
    "patio_heater": {"status": "off"},
    "garage_charger": {"status": "off"},

    # Health & Misc
    "medicine_cabinet": {"status": "locked"},
    "smart_scale": {"status": "off"},
    "sleep_tracker": {"status": "off"},
    "baby_monitor": {"status": "off"},
    "pet_feeder": {"status": "off"},
    "smart_blinds": {"status": "closed"},
    "smart_curtains": {"status": "closed"},
    "smart_mirror": {"status": "off"},
    "aroma_diffuser": {"status": "off"},
    "3d_printer": {"status": "off"},
    "solar_panel_controller": {"status": "on", "output_kw": 2.5},
    "backup_generator": {"status": "off"},
    "smart_meter": {"status": "on", "power_usage": "1.2kW"},
}
def list_devices():
    return {
        # Lighting
        "bedroom light": {"type": "lighting", "location": "bedroom"},
        "living room light": {"type": "lighting", "location": "living room"},
        "kitchen light": {"type": "lighting", "location": "kitchen"},
        "bathroom light": {"type": "lighting", "location": "bathroom"},
        "hallway light": {"type": "lighting", "location": "hallway"},

        # Doors
        "front door": {"type": "door", "location": "front"},
        "back door": {"type": "door", "location": "back"},
        "garage door": {"type": "door", "location": "garage"},

        # Kitchen appliances
        "microwave": {"type": "appliance", "location": "kitchen"},
        "oven": {"type": "appliance", "location": "kitchen"},
        "stove": {"type": "appliance", "location": "kitchen"},
        "coffee maker": {"type": "appliance", "location": "kitchen"},
        "kettle": {"type": "appliance", "location": "kitchen"},

        # Climate devices
        "humidifier": {"type": "climate", "location": "living room"},
        "air conditioner": {"type": "climate", "location": "bedroom"},
        "heater": {"type": "climate", "location": "living room"},

        # Bathroom devices
        "bath fan": {"type": "bathroom", "location": "bathroom"},
        "shower": {"type": "bathroom", "location": "bathroom"},

        # Security / Cameras
        "security camera 1": {"type": "security", "location": "front"},
        "security camera 2": {"type": "security", "location": "back"},
        "alarm system": {"type": "security", "location": "whole house"},

        # Outdoor
        "sprinkler": {"type": "outdoor", "location": "garden"},
        "garage light": {"type": "outdoor", "location": "garage"},
        "outdoor lights": {"type": "outdoor", "location": "yard"},

        # Robots / Laundry
        "robot vacuum": {"type": "robot", "location": "whole house"},
        "washing machine": {"type": "appliance", "location": "laundry room"},
        "dryer": {"type": "appliance", "location": "laundry room"},

        # Medicine / Cabinet
        "medicine cabinet": {"type": "medicine", "location": "bathroom"},
    }

def extract_device_and_action(command):
    devices = list_devices()
    command_lower = command.lower()
    
    for device_name in devices.keys():
        if device_name in command_lower:
            # look for numeric value if needed
            words = command_lower.split()
            value = None
            for w in words:
                try:
                    value = float(w.strip('%'))  # handle percentages too
                    break
                except ValueError:
                    continue
            return device_name, value
    return None, None

def control_device(device: str, location: str = "all", action: str = "get_status"):
    from intent_firewall import intent_firewall
    print(f"[API] control_device called: device='{device}', location='{location}', action='{action}'")

    allowed, msg, confirm = intent_firewall(
        {"device": device, "location": location, "action": action},
        system_state=device_states,
        raw_text=f"{action} {device} {location}",
    )

    if not allowed and not confirm:
        return msg
    if confirm:
        return msg

    matched_devices = []
    device_lower = device.lower()
    location_lower = location.lower()

    for dev_name in device_states:
        dev_name_lower = dev_name.lower()
        device_match = (
            device_lower == "all"
            or device_lower in dev_name_lower
            or (device_lower == "light" and "light" in dev_name_lower)
            or (device_lower == "thermostat" and "thermostat" in dev_name_lower)
        )
        location_match = location_lower == "all" or location_lower in dev_name_lower
        if device_match and location_match:
            matched_devices.append(dev_name)

    if not matched_devices:
        return f"No devices found matching: device='{device}', location='{location}'"

    results = []
    for dev_name in matched_devices:
        dev = device_states[dev_name]

        if action in ["turn_on", "on", "start"]:
            dev["status"] = "on"
            result = f"✅ Turned on {dev_name.replace('_', ' ')}"
        elif action in ["turn_off", "off", "stop"]:
            dev["status"] = "off"
            result = f"✅ Turned off {dev_name.replace('_', ' ')}"
        elif action in ["lock"]:
            dev["status"] = "locked"
            result = f"🔒 Locked {dev_name.replace('_', ' ')}"
        elif action in ["unlock"]:
            dev["status"] = "unlocked"
            result = f"🔓 Unlocked {dev_name.replace('_', ' ')}"
        elif action in ["open"]:
            dev["status"] = "open"
            result = f"🚪 Opened {dev_name.replace('_', ' ')}"
        elif action in ["close"]:
            dev["status"] = "closed"
            result = f"🚪 Closed {dev_name.replace('_', ' ')}"
        elif action in ["get_status", "status"]:
            status_info = ", ".join(f"{k}={v}" for k, v in dev.items())
            result = f"📊 {dev_name.replace('_', ' ')}: {status_info}"
        else:
            result = f"⚠️ Unknown action '{action}' for {dev_name.replace('_', ' ')}"

        explanation = generate_rich_explanation(dev_name, action, result)
        results.append(explanation)

    return "\n\n".join(results)


# =========================
# Rich XAI Explanations for all devices
# =========================
def generate_rich_explanation(device: str, action: str, result: str):
    base = device.replace("_", " ").title()

    explanations = {
        "smart_thermostat": "🌡️ Adaptive climate control optimizes comfort while saving energy.",
        "air_conditioner": "❄️ Cooling system adjusts airflow based on room occupancy sensors.",
        "heater": "🔥 Smart heating balances warmth with cost-efficiency.",
        "humidifier": "💧 Maintains ideal humidity levels for health and comfort.",
        "dehumidifier": "🌫️ Removes excess moisture, preventing mold and allergies.",
        "air_purifier": "🌬️ Filters pollutants with AI-based air quality monitoring.",

        "bedroom_light": "💡 Auto-dimming lights for better sleep hygiene.",
        "kitchen_light": "🍳 Brightness optimized for cooking visibility.",
        "living_room_light": "🛋️ Ambient presets for relaxation or gatherings.",
        "bathroom_light": "🚿 Anti-fog smart lighting for visibility.",
        "garden_light": "🌱 Solar-synced outdoor lighting.",
        "stair_light": "🪜 Motion-activated stair safety lighting.",
        "garage_light": "🚗 Auto-on when car approaches.",
        "chandelier": "✨ Smart chandelier with dimming + scheduling.",
        "led_strip": "🌈 Mood lighting with color presets.",

        "front_door": "🚪 Smart lock with biometric + PIN options.",
        "back_door": "🔒 Reinforced smart locking.",
        "garage_door": "🚘 Remote access + intrusion detection.",
        "balcony_door": "🏡 Auto-lock for safety.",
        "security_camera": "👁️ AI detects people, pets, and packages.",
        "doorbell_camera": "📦 Smart notifications for deliveries.",
        "window_sensor": "🪟 Alerts if window opened unexpectedly.",
        "alarm_system": "🚨 Multi-sensor intrusion prevention.",
        "motion_detector": "🕵️ AI distinguishes pets from humans.",

        "smart_oven": "🔥 Auto-adjust cooking programs with safety shutoff.",
        "stove": "🍲 Heat sensors prevent unattended fire risks.",
        "microwave": "⚡ Detects food weight for auto-timing.",
        "toaster": "🍞 Smart browning control.",
        "coffee_machine": "☕ Brews on schedule with bean freshness tracking.",
        "blender": "🥤 Safety lock prevents accidents.",
        "food_processor": "🔪 Auto-speed adjustment for tasks.",
        "dishwasher": "💦 Water-saving cycles with AI load detection.",
        "fridge": "🧊 Monitors freshness + energy usage.",
        "freezer": "❄️ Smart defrost cycles.",
        "pressure_cooker": "🍲 Auto shut-off after cooking.",

        "smart_tv": "📺 AI sound + picture optimization.",
        "gaming_console": "🎮 Auto cooling + performance boost.",
        "projector": "📽️ Adjusts brightness for ambient light.",
        "smart_speaker": "🎶 Adaptive EQ + voice assistant.",
        "home_theater": "🔊 Surround sound calibration.",

        "robot_vacuum": "🤖 Maps + cleans efficiently with AI routing.",
        "robot_lawn_mower": "🌿 Smart lawn trimming with obstacle detection.",
        "washing_machine": "🧺 AI wash cycles save water + energy.",
        "dryer": "🌬️ Auto-stop when clothes dry.",
        "steam_iron": "👕 Temp control prevents fabric burns.",

        "water_heater": "🚿 Prevents scalding, optimizes heating times.",
        "smart_shower": "💦 Custom temperature + water-saving.",
        "bath_exhaust_fan": "💨 Humidity-triggered ventilation.",
        "toothbrush_sanitizer": "🪥 UV sterilization for hygiene.",

        "pool_pump": "🏊 Keeps water clean with smart cycles.",
        "pool_heater": "🔥 Maintains optimal swimming temp.",
        "hot_tub": "🛁 Smart bubbles + heating.",
        "sprinkler_system": "🌧️ Weather-based irrigation.",
        "outdoor_grill": "🍖 Monitors cooking temp remotely.",
        "garden_irrigation": "🌱 Soil-moisture-driven watering.",
        "patio_heater": "🔥 Outdoor comfort on demand.",
        "garage_charger": "⚡ Smart EV charging with cost-optimization.",

        "medicine_cabinet": "💊 Auto-lock + inventory tracking.",
        "smart_scale": "⚖️ Tracks weight + syncs with health apps.",
        "sleep_tracker": "😴 Monitors sleep quality.",
        "baby_monitor": "👶 Sends smart alerts to phone.",
        "pet_feeder": "🐾 Dispenses meals on schedule.",
        "smart_blinds": "🪟 Auto-open with sunrise.",
        "smart_curtains": "🌇 Automated closing at sunset.",
        "smart_mirror": "🪞 Displays health + weather info.",
        "aroma_diffuser": "🌸 Releases scents based on mood.",
        "3d_printer": "🖨️ Auto-pauses if filament runs out.",
        "solar_panel_controller": "☀️ Tracks energy harvest.",
        "backup_generator": "🔋 Activates during power outage.",
        "smart_meter": "📊 Monitors real-time energy use.",
    }

    explanation = explanations.get(device.lower(), "✅ Command Executed")
    return f"{explanation}\n\n📋 **System Status**: {result}"
