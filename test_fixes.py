# test_fixes.py - Test the Unicode and location fixes

import sys
import os

# Add current directory to Python path
sys.path.insert(0, os.getcwd())

def test_location_normalization():
    """Test the location normalization logic"""
    print("🧪 Testing Location Normalization...")
    print("=" * 40)
    
    from llm_interface import normalize_command
    
    test_cases = [
        {"device": "light", "location": "unknown", "action": "turn_on"},
        {"device": "light", "location": "", "action": "turn_on"},
        {"device": "light", "location": "all_rooms", "action": "turn_on"},
        {"device": "light", "location": "livingroom", "action": "turn_on"},
        {"device": "light", "location": "current", "action": "turn_on"},
    ]
    
    for i, cmd in enumerate(test_cases, 1):
        original = cmd.copy()
        normalized = normalize_command(cmd)
        print(f"Test {i}:")
        print(f"  Input:  {original}")
        print(f"  Output: {normalized}")
        print()

def test_device_matching():
    """Test device matching in smart_home_api"""
    print("🔍 Testing Device Matching...")
    print("=" * 40)
    
    from smart_home_api import control_device
    
    test_commands = [
        ("light", "all", "turn_on"),
        ("light", "bedroom", "turn_on"),
        ("light", "unknown_location", "turn_on"),
        ("lights", "kitchen", "get_status"),
        ("nonexistent", "bedroom", "turn_on"),
    ]
    
    for i, (device, location, action) in enumerate(test_commands, 1):
        print(f"Test {i}: control_device('{device}', '{location}', '{action}')")
        try:
            result = control_device(device, location, action)
            print(f"  Result: {result}")
        except Exception as e:
            print(f"  Error: {e}")
        print()

def test_unicode_handling():
    """Test Unicode handling (simulate without calling Ollama)"""
    print("📝 Testing Unicode Handling...")
    print("=" * 40)
    
    # Simulate problematic characters that might come from Ollama
    test_strings = [
        "Normal ASCII text",
        "Text with unicode: café, naïve, résumé",
        "Mixed encoding test: " + bytes([0x8f, 0x9d]).decode('cp1252', errors='replace'),
    ]
    
    for i, test_str in enumerate(test_strings, 1):
        print(f"Test {i}: {repr(test_str)}")
        try:
            # Test encoding/decoding round trip
            encoded = test_str.encode('utf-8')
            decoded = encoded.decode('utf-8')
            print(f"  UTF-8 round trip: ✅ Success")
        except Exception as e:
            print(f"  UTF-8 round trip: ❌ {e}")
        
        try:
            # Test cp1252 fallback
            encoded = test_str.encode('cp1252', errors='replace')
            decoded = encoded.decode('cp1252', errors='replace')
            print(f"  CP1252 fallback: ✅ Success")
        except Exception as e:
            print(f"  CP1252 fallback: ❌ {e}")
        print()

def main():
    print("🔧 Smart Home Agent - Fix Verification Tests")
    print("=" * 60)
    print()
    
    try:
        test_location_normalization()
        test_device_matching()
        test_unicode_handling()
        
        print("✅ All tests completed!")
        print()
        print("💡 Next steps:")
        print("1. Run: python main.py")
        print("2. Try commands like: 'turn on the lights'")
        print("3. The Unicode issue should be resolved")
        print("4. Location 'unknown' should now map to 'all'")
        
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("Make sure all required files are in the current directory:")
        print("- llm_interface.py")
        print("- smart_home_api.py") 
        print("- intent_firewall.py")
        print("- rag_engine.py")
        print("- state_manager.py")
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()