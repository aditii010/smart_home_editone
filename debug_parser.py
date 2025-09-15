# debug_parser.py - Test the JSON parsing function

import json
import re

def normalize_command(cmd):
    if isinstance(cmd, dict):
        device = cmd.get("device", "").lower().replace(" ", "_")
        location = cmd.get("location", "").lower().replace(" ", "_")

        # Normalize device
        if device in ["all_lights", "lights", "lightbulbs", "lamps"]:
            cmd["device"] = "light"
        else:
            cmd["device"] = device.replace("_", " ")

        # Enhanced location normalization
        location_mapping = {
            "all_rooms": "all",
            "entire_house": "all", 
            "whole_home": "all",
            "all": "all",
            "unknown": "all",
            "current": "living room",
            "here": "living room",
            "this_room": "living room",
            "livingroom": "living room",
            "kids_room": "kids room",
            "front_door": "front door",
            "": "all"
        }

        normalized_location = location_mapping.get(location, location.replace("_", " "))
        cmd["location"] = normalized_location

        if not cmd.get("location") or cmd["location"].strip() in ["", "unknown"]:
            cmd["location"] = "all"

    return cmd

def safe_parse_multiple_json(raw_output):
    """Enhanced JSON parser with detailed debugging"""
    print(f"🔍 DEBUG: Raw input: {repr(raw_output)}")
    
    if not raw_output or not raw_output.strip():
        print("❌ DEBUG: Empty input")
        return None
        
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw_output.strip(), flags=re.MULTILINE)
    print(f"🔍 DEBUG: Cleaned input: {repr(cleaned)}")

    # First try to parse as complete JSON
    try:
        parsed = json.loads(cleaned)
        print(f"✅ DEBUG: Successfully parsed as complete JSON: {type(parsed)}")
        if isinstance(parsed, dict):
            result = [normalize_command(parsed)]
            print(f"✅ DEBUG: Returning single dict as list: {result}")
            return result
        elif isinstance(parsed, list):
            result = [normalize_command(p) for p in parsed]
            print(f"✅ DEBUG: Returning normalized list: {result}")
            return result
    except json.JSONDecodeError as e:
        print(f"⚠️ DEBUG: Failed to parse as complete JSON: {e}")

    # Try to parse individual JSON objects using regex
    print("🔍 DEBUG: Trying regex-based parsing...")
    objects = []
    for match in re.finditer(r"{.*?}", cleaned, flags=re.DOTALL):
        print(f"🔍 DEBUG: Found JSON-like match: {match.group()}")
        try:
            obj = json.loads(match.group())
            normalized = normalize_command(obj)
            objects.append(normalized)
            print(f"✅ DEBUG: Successfully parsed and normalized: {normalized}")
        except json.JSONDecodeError as e:
            print(f"❌ DEBUG: Failed to parse match: {e}")

    # If we found objects, return them
    if objects:
        print(f"✅ DEBUG: Returning {len(objects)} objects from regex parsing")
        return objects

    # Final attempt: try to parse as a JSON string that contains JSON
    print("🔍 DEBUG: Trying nested JSON string parsing...")
    try:
        # Handle cases where LLM returns '["json_string"]' or similar
        if cleaned.startswith('[') and cleaned.endswith(']'):
            parsed_list = json.loads(cleaned)
            print(f"🔍 DEBUG: Parsed as list: {parsed_list}")
            if isinstance(parsed_list, list) and len(parsed_list) > 0:
                # Try to parse each string element as JSON
                result_objects = []
                for i, item in enumerate(parsed_list):
                    print(f"🔍 DEBUG: Processing list item {i}: {repr(item)} (type: {type(item)})")
                    if isinstance(item, str):
                        try:
                            parsed_item = json.loads(item)
                            print(f"✅ DEBUG: Parsed string item as JSON: {parsed_item}")
                            if isinstance(parsed_item, dict):
                                normalized = normalize_command(parsed_item)
                                result_objects.append(normalized)
                                print(f"✅ DEBUG: Added normalized item: {normalized}")
                        except json.JSONDecodeError as e:
                            print(f"❌ DEBUG: Failed to parse string item: {e}")
                    elif isinstance(item, dict):
                        normalized = normalize_command(item)
                        result_objects.append(normalized)
                        print(f"✅ DEBUG: Added dict item: {normalized}")
                
                if result_objects:
                    print(f"✅ DEBUG: Returning {len(result_objects)} objects from nested parsing")
                    return result_objects
    except json.JSONDecodeError as e:
        print(f"❌ DEBUG: Failed nested JSON parsing: {e}")

    print("❌ DEBUG: All parsing methods failed")
    return None

def test_parsing():
    """Test the parsing function with various inputs"""
    test_cases = [
        # Normal cases
        '{"device": "thermostat", "location": "all", "action": "turn_on"}',
        '[{"device": "light", "location": "bedroom", "action": "turn_on"}]',
        
        # Problematic case from your error
        '["{\\"device\\": \\"thermostat\\", \\"location\\": \\"all\\", \\"action\\": \\"turn_on\\"}"]',
        
        # Edge cases
        '[]',
        '',
        'invalid json',
        '{"incomplete": "command"}',
    ]
    
    print("🧪 Testing JSON Parsing Function")
    print("=" * 50)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🔬 Test Case {i}:")
        print(f"Input: {repr(test_case)}")
        result = safe_parse_multiple_json(test_case)
        print(f"Result: {result}")
        print("-" * 30)

if __name__ == "__main__":
    test_parsing()