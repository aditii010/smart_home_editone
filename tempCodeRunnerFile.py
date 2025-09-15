 # main.py
import time
import difflib
from process_commands import process_commands
from llm_interface import query_llm
from rag_engine import RAGEngine
from state_manager import StateManager
from smart_home_api import list_devices, control_device
from vision_module import VisionModule
from vision_intents import derive_commands_from_vision, map_child_location
import difflib

def normalize_name(name: str) -> str:
    """Normalize device/location names for consistent lookup."""
    if not name:
        return ""
    name = name.lower().strip()

    # Simple keyword-based normalization
    replacements = {
        "smart tv": "tv",
        "television": "tv",
        "where the child is standing": "living room",  # fallback assumption
        "child standing": "living room",
        "child is near": "",
    }
    for k, v in replacements.items():
        if k in name:
            name = name.replace(k, v)

    return name.strip()

def execute_action(commands, device_registry):
    """Execute parsed LLM/Vision commands with fuzzy matching + normalization."""
    for cmd in commands:
        device = normalize_name(cmd.get("device", ""))
        location = normalize_name(cmd.get("location", ""))
        action = cmd.get("action", "")

        # Build canonical key
        target = f"{device} ({location})".strip()

        if target in device_registry:
            print(f"✅ Action executed: {target} - {action}")
        else:
            # Try fuzzy matching
            possible = difflib.get_close_matches(target, device_registry.keys(), n=1, cutoff=0.5)
            if possible:
                match = possible[0]
                print(f"✅ Action executed (fuzzy match): {match} - {action}")
            else:
                print(f"❌ No such device found (even after fuzzy match): {target}")


def main():
    print("💡 Smart Home CLI with RAG + Vision AI (Type 'exit' to quit')")

    rag = RAGEngine(kb_path="knowledge.txt")
    state = StateManager(context_file="data/context_summary.json")
    vision = VisionModule()

    # You can periodically update this to your latest CCTV frame
    default_image_path = "frames/latest.jpg"

    while True:
        user_input = input("\nYou: ").strip()
        if user_input.lower() in ["exit", "quit"]:
            break

        # --- Optional: per-command image path override ---
        #   Example: "use frame: frames/livingroom.jpg; turn on the tv where the child is standing"
        image_path = default_image_path
        if "use frame:" in user_input.lower():
            try:
                prefix, rest = user_input.split(":", 1)
                frame_path, actual_text = rest.split(";", 1)
                image_path = frame_path.strip()
                user_input = actual_text.strip()
            except Exception:
                pass

        # --- Analyze current image frame (non-blocking if missing) ---
        try:
            image_context = vision.analyze_frame(image_path)
            print(f"[Vision] {image_path} → {len(image_context.get('detections', []))} detections, "
                  f"{len(image_context.get('relations', []))} relations")
        except Exception as e:
            print(f"[Vision] Skipping image analysis ({e})")
            image_context = None

        # --- Built-ins ---
        lower = user_input.lower()
        if lower in ["list devices", "what can i control", "show devices",
                     "what devices can i control", "what are the devices available to me"]:
            devices = list_devices()
            print("📋 Devices you can control:")
            for d in devices:
                print(f"- {d}")
            continue

        if lower in ["status of all devices", "show status", "device status", "status"]:
            responses = control_device("*", "*", "get_status")
            print("📊 Current device status:")
            print(responses)
            continue

        # --- Parse as structured device control using LLM ---
        commands = None
        for attempt in range(1, 2+1):
            print(f"[LLM] Attempt {attempt} querying with input: {user_input}")
            commands = query_llm(user_input)
            print(f"[LLM] Parsed commands: {commands}")
            if commands:
                break
            else:
                print(f"[LLM] Retrying in 2 seconds...")
                time.sleep(2)

        # --- Derive extra commands from Vision (works even if LLM returned None) ---
        vision_cmds = derive_commands_from_vision(user_input, image_context)
        if vision_cmds:
            print(f"[Vision] Derived commands: {vision_cmds}")

        # --- Combine and dedupe ---
        combined = (commands or []) + vision_cmds

        if not combined:
            # fallback to RAG if neither LLM nor Vision gave commands
            answer = rag.query(user_input)
            print(f"Agent: {answer}")
            continue   # ✅ still inside while loop

        # --- Map child locations to real rooms ---
        combined = map_child_location(combined, image_context)

        # --- Execute combined structured commands ---
        responses = process_commands(combined, user_input)
        for res in responses:
            print(res)

        # --- Update state for each command ---
        for cmd in combined:
            device_name = cmd.get("device") or "unknown"
            location = cmd.get("location") or "unknown"
            action = cmd.get("action") or "unknown"
            state.update_state(device_name, location, action)


if __name__ == "__main__":
    main()
