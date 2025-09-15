import difflib
import sys
import os

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from smart_home_api import control_device, list_devices

# ----------------------------
# Helper Functions
# ----------------------------

def normalize_name(name: str) -> str:
    """Normalize device/location names for consistent lookup."""
    if not name:
        return ""
    name = name.lower().strip()
    replacements = {
        "smart tv": "tv",
        "television": "tv",
        "where the child is standing": "living room",
        "child standing": "living room",
        "child is near": "",
    }
    for k, v in replacements.items():
        if k in name:
            name = name.replace(k, v)
    return name.strip()


def is_query(text: str) -> bool:
    """Detect if input is a query rather than a control command."""
    triggers = ["why", "how", "what", "explain", "reason"]
    text_lower = text.lower()
    return any(text_lower.startswith(word) for word in triggers)


def process_commands(commands, original_text):
    """Execute structured commands with normalization + fuzzy matching."""
    responses = []
    device_registry = list_devices()

    context = {
        "original_text": original_text,
        "child_nearby": "child" in original_text.lower(),
        "pet_nearby": "dog" in original_text.lower() or "cat" in original_text.lower()
    }

    for cmd in commands:
        device = normalize_name(cmd.get("device", ""))
        location = normalize_name(cmd.get("location", ""))
        action = cmd.get("action", "")

        target = f"{device} ({location})".strip()

        if target in device_registry:
            responses.append(f"✅ Action executed: {target} - {action}")
            try:
                control_device(device, location, action, context)
            except TypeError:
                control_device(device, location, action)
        else:
            # Try fuzzy match
            possible = difflib.get_close_matches(target, device_registry, n=1, cutoff=0.5)
            if possible:
                match = possible[0]
                responses.append(f"✅ Action executed through VisionAI: {match} - {action}")
                if " (" in match and match.endswith(")"):
                    d, loc = match.split(" (", 1)
                    loc = loc.rstrip(")")
                else:
                    d, loc = match, ""
                try:
                    control_device(d.strip(), loc.strip(), action, context)
                except TypeError:
                    control_device(d.strip(), loc.strip(), action)
            else:
                responses.append(f"❌ No such device found: {target}")

    return responses


# ----------------------------
# Main Loop
# ----------------------------

def smart_home_loop():
    print("🏠 SMART HOME ASSISTANT - XAI EDITION")
    print("💬 Rich explanations and intelligent control!")
    print("🚪 Type 'exit' to quit")
    print("="*60)

    while True:
        user_input = input("🎙️ You: ").strip()
        if user_input.lower() == "exit":
            print("👋 Goodbye!")
            break

        # --- XAI / Query Detection ---
        if is_query(user_input):
            print(f"[XAI] Explanation: The system interprets your question '{user_input}' and provides insight...")
            # Here you can implement actual reasoning from logs/context if needed
            continue

        # --- Intent Firewall ---
        # This is a simplified example
        blocked_terms = ["self destruct", "unlock safe", "open vault"]
        if any(term in user_input.lower() for term in blocked_terms):
            print("⚠️ Action blocked by Intent Firewall: unsafe command detected!")
            continue

        # --- Normal Control ---
        # Here we assume `llm_parse_to_commands` converts text -> structured command dicts
        try:
            commands = llm_parse_to_commands(user_input)  # replace with your LLM parser
        except Exception:
            print("❌ Failed to parse command.")
            continue

        responses = process_commands(commands, user_input)
        for r in responses:
            print(r)


# ----------------------------
# Run the Assistant
# ----------------------------
if __name__ == "__main__":
    smart_home_loop()
