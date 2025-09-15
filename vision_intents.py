# vision_intents.py
"""
Convert image context + user text into extra structured commands.

Supported devices via vision:
- smart_tv
- smart_oven (also matches stove/microwave)
- livingroom_light / lights
- smart_thermostat
- robot_vacuum
- sprinkler_system
- security_camera
- (optional) smart_lock / front_door via 'door' proximity
"""

def _cmd(device, location, action, value=None):
    c = {"device": device, "location": location, "action": action}
    if value is not None:
        c["value"] = value
    return c

def _any_near(image_context, object_name):
    return any(rel.get("subject") == "person" and
               rel.get("relation") == "near" and
               rel.get("object") == object_name
               for rel in image_context.get("relations", []))

def derive_commands_from_vision(user_text, image_context):
    """
    Generate extra device commands leveraging what the camera sees.
    Returns a list of commands same shape as LLM parser:
      [{"device":..., "location":..., "action":..., "value":...}, ...]
    """
    if not image_context:
        return []

    text = (user_text or "").lower()
    rels = image_context.get("relations", [])
    dets = image_context.get("detections", [])

    commands = []

    # 1) TV: “turn on the tv where the child/person is standing”, “play”, “mute if nobody there”
    if "tv" in text or "television" in text or "screen" in text:
        if _any_near(image_context, "tv"):
            # Person near TV → operate living room TV (assumption)
            if any(k in text for k in ["turn on", "switch on", "play"]):
                commands.append(_cmd("smart_tv", "living room", "turn_on"))
            if "mute" in text:
                commands.append(_cmd("smart_tv", "living room", "set_volume", 0))
            if "turn off" in text or "switch off" in text:
                commands.append(_cmd("smart_tv", "living room", "turn_off"))

    # If a person near TV but user asked generic “turn on tv where child is standing”
    if ("turn on" in text and "tv" in text and "where" in text) and _any_near(image_context, "tv"):
        commands.append(_cmd("smart_tv", "living room", "turn_on"))

    # 2) Oven/Stove: “child near oven, turn it off” / “preheat if someone is in kitchen”
    if "oven" in text or "stove" in text or "microwave" in text:
        if _any_near(image_context, "oven"):
            if any(k in text for k in ["turn off", "switch off", "stop"]):
                commands.append(_cmd("smart_oven", "kitchen", "turn_off"))
            if any(k in text for k in ["turn on", "preheat", "start"]):
                commands.append(_cmd("smart_oven", "kitchen", "turn_on"))

    # “child is near oven, turn it off” even if not explicitly saying oven in text
    if ("child" in text or "kid" in text or "person" in text) and _any_near(image_context, "oven"):
        if any(k in text for k in ["turn off", "switch off", "stop", "make safe", "shut"]):
            commands.append(_cmd("smart_oven", "kitchen", "turn_off"))

    # 3) Lights: “lights where the person is → on”, “dim if nobody around screen/sofa”
    if "light" in text or "lights" in text or "lamp" in text:
        if _any_near(image_context, "seating_area") or _any_near(image_context, "tv"):
            if any(k in text for k in ["turn on", "switch on"]):
                commands.append(_cmd("livingroom_light", "living room", "turn_on"))
            if "dim" in text:
                commands.append(_cmd("livingroom_light", "living room", "set_brightness", 40))
            if "turn off" in text:
                commands.append(_cmd("livingroom_light", "living room", "turn_off"))

    # 4) Thermostat: presence-based tweaks
    if "thermostat" in text or "temperature" in text:
        if any(r["subject"] == "person" for r in rels):
            # If people present, a gentle comfort nudge if user asks
            if any(k in text for k in ["warmer", "increase", "raise", "heat"]):
                commands.append(_cmd("smart_thermostat", "hallway", "set_temperature", 24))
            if any(k in text for k in ["cooler", "decrease", "lower", "ac"]):
                commands.append(_cmd("smart_thermostat", "hallway", "set_temperature", 20))

    # 5) Robot vacuum: avoid if people in seating area; start if user asks and no one near seating
    if "vacuum" in text or "robot" in text or "clean" in text:
        if "start" in text or "begin" in text:
            if not _any_near(image_context, "seating_area"):
                commands.append(_cmd("robot_vacuum", "living room", "start"))
        if "dock" in text or "stop" in text or "pause" in text:
            commands.append(_cmd("robot_vacuum", "living room", "dock"))

    # 6) Sprinklers: don’t run if people detected on lawn (if your camera watches lawn)
    if "sprinkler" in text or "sprinklers" in text or "water lawn" in text:
        # If people are in frame and user says start, choose not to add start (pure vision logic)
        if "start" in text or "run" in text or "turn on" in text:
            if not any(d["label"] == "person" for d in dets):
                commands.append(_cmd("sprinkler_system", "front yard", "start"))
        if "stop" in text or "turn off" in text:
            commands.append(_cmd("sprinkler_system", "front yard", "stop"))

    # 7) Security camera: if user mentions “where person is” → focus, record, snapshot
    if "camera" in text or "security" in text:
        if any(d["label"] == "person" for d in dets):
            if "record" in text or "start recording" in text:
                commands.append(_cmd("security_camera", "entryway", "start_recording"))
            if "snapshot" in text or "photo" in text or "snap" in text:
                commands.append(_cmd("security_camera", "entryway", "snapshot"))
            if "on" in text or "enable" in text:
                commands.append(_cmd("security_camera", "entryway", "turn_on"))
            if "off" in text or "disable" in text:
                commands.append(_cmd("security_camera", "entryway", "turn_off"))

    # 8) Door/Lock: “open/lock the door where the person is”
    if "door" in text or "lock" in text:
        if _any_near(image_context, "door"):
            if "unlock" in text or "open" in text:
                commands.append(_cmd("smart_lock", "front door", "unlock"))
            if "lock" in text or "close" in text:
                commands.append(_cmd("smart_lock", "front door", "lock"))

    # Dedup (device+location+action)
    seen = set()
    deduped = []
    for c in commands:
        key = (c.get("device"), c.get("location"), c.get("action"), c.get("value"))
        if key not in seen:
            seen.add(key)
            deduped.append(c)
            
            # --- New helper: map "child/person standing" → actual room from vision ---
def map_child_location(commands, image_context):
    """
    Replace fake locations like 'child standing' with actual rooms (living room, kitchen, etc.)
    based on vision detections/relations.
    """
    if not image_context:
        return commands

    dets = image_context.get("detections", [])
    rels = image_context.get("relations", [])

    # Simple heuristic: check if person near a known object → assign that room
    room_guess = None
    if any(r["subject"] == "person" and r["object"] == "tv" for r in rels):
        room_guess = "living room"
    elif any(r["subject"] == "person" and r["object"] == "oven" for r in rels):
        room_guess = "kitchen"
    elif any(r["subject"] == "person" and r["object"] == "door" for r in rels):
        room_guess = "entryway"
    elif any(r["subject"] == "person" and r["object"] == "seating_area" for r in rels):
        room_guess = "living room"

    updated = []
    for cmd in commands:
        loc = cmd.get("location", "")
        if "child" in loc or "person" in loc:
            if room_guess:
                cmd["location"] = room_guess
        updated.append(cmd)
    return updated


   
