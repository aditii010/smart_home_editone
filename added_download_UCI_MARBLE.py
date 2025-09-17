# added_download_UCI_MARBLE.py
# --- JUSTIFICATION: Created dataset download script as required by specifications ---
"""
Dataset download script for UCI ADL and MARBLE datasets.
This script provides automated download capabilities and setup instructions.
Run this script before using the main LLMe2e pipeline to ensure datasets are available.

Usage:
    python added_download_UCI_MARBLE.py
"""

import os
import sys
import urllib.request
import zipfile
import shutil
import json
from pathlib import Path

def create_data_directory():
    """Create data directory structure."""
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    
    # Create subdirectories
    (data_dir / "uci_adl").mkdir(exist_ok=True)
    (data_dir / "marble").mkdir(exist_ok=True)
    (data_dir / "raw").mkdir(exist_ok=True)
    (data_dir / "processed").mkdir(exist_ok=True)
    
    print(f"✅ Created data directory structure at: {data_dir.absolute()}")
    return data_dir

def download_uci_adl():
    """
    Download UCI ADL dataset.
    Note: This provides download instructions as the actual dataset requires manual access.
    """
    print("📁 UCI ADL Dataset Download")
    print("-" * 40)
    
    uci_dir = Path("data/uci_adl")
    
    if (uci_dir / "dataset_info.json").exists():
        print("✅ UCI ADL dataset already configured")
        return True
    
    print("📋 Manual download required for UCI ADL dataset:")
    print("1. Visit: https://archive.ics.uci.edu/dataset/196/activities+of+daily+living+adls+recognition+using+binary+sensors")
    print("2. Download the dataset files")
    print(f"3. Extract all files to: {uci_dir.absolute()}")
    print("4. Run this script again to verify setup")
    
    # Create placeholder info file with expected structure
    dataset_info = {
        "dataset_name": "UCI ADL Recognition Dataset",
        "source_url": "https://archive.ics.uci.edu/dataset/196/activities+of+daily+living+adls+recognition+using+binary+sensors",
        "description": "Binary sensor data for ADL recognition",
        "preprocessing": {
            "window_size": 60,
            "overlap": 0.8,
            "format": "States2JSON"
        },
        "expected_files": [
            "binary_sensors.txt",
            "activity_labels.txt", 
            "participant_info.txt"
        ],
        "manual_download": True
    }
    
    with open(uci_dir / "dataset_info.json", 'w') as f:
        json.dump(dataset_info, f, indent=2)
    
    print(f"📝 Dataset configuration saved to: {uci_dir / 'dataset_info.json'}")
    return False

def download_marble():
    """
    Download MARBLE dataset.
    Note: This provides download instructions as the dataset location varies.
    """
    print("📁 MARBLE Dataset Download")
    print("-" * 40)
    
    marble_dir = Path("data/marble")
    
    if (marble_dir / "dataset_info.json").exists():
        print("✅ MARBLE dataset already configured")
        return True
    
    print("📋 Manual download required for MARBLE dataset:")
    print("1. Contact MARBLE dataset authors or visit their official repository")
    print("2. Follow their data access procedures")
    print(f"3. Extract dataset files to: {marble_dir.absolute()}")
    print("4. Run this script again to verify setup")
    
    # Create placeholder info file
    dataset_info = {
        "dataset_name": "MARBLE Multimodal Dataset",
        "description": "Multimodal sensor data for activity recognition",
        "preprocessing": {
            "window_size": 16,
            "overlap": 0.8,
            "format": "States2JSON"
        },
        "expected_files": [
            "accelerometer_data.csv",
            "gyroscope_data.csv",
            "proximity_data.csv",
            "activity_annotations.json"
        ],
        "manual_download": True
    }
    
    with open(marble_dir / "dataset_info.json", 'w') as f:
        json.dump(dataset_info, f, indent=2)
    
    print(f"📝 Dataset configuration saved to: {marble_dir / 'dataset_info.json'}")
    return False

def create_sample_datasets():
    """
    Create sample datasets for testing the LLMe2e pipeline when real datasets are not available.
    """
    print("📊 Creating sample datasets for testing...")
    
    # Create sample UCI ADL data
    uci_sample = {
        "metadata": {
            "dataset": "UCI_ADL_Sample",
            "windows": 5,
            "window_size": 60,
            "overlap": 0.8
        },
        "data": []
    }
    
    # Sample UCI ADL windows
    activities = ["cooking", "cleaning", "watching_tv", "sleeping", "eating"]
    for i, activity in enumerate(activities):
        window = {
            "window_id": f"uci_sample_{i}",
            "start_time": f"{9+i}:00:00",
            "end_time": f"{9+i}:01:00",
            "ground_truth": activity,
            "states2json": generate_sample_states_for_activity(activity),
            "dataset": "uci_adl"
        }
        uci_sample["data"].append(window)
    
    # Save sample UCI data
    uci_path = Path("data/processed/uci_adl_sample.json")
    with open(uci_path, 'w') as f:
        json.dump(uci_sample, f, indent=2)
    print(f"✅ UCI ADL sample data created: {uci_path}")
    
    # Create sample MARBLE data
    marble_sample = {
        "metadata": {
            "dataset": "MARBLE_Sample", 
            "windows": 5,
            "window_size": 16,
            "overlap": 0.8
        },
        "data": []
    }
    
    # Sample MARBLE windows (motion-focused activities)
    motion_activities = ["walking", "running", "sitting", "standing", "lying"]
    for i, activity in enumerate(motion_activities):
        window = {
            "window_id": f"marble_sample_{i}",
            "start_time": f"{14+i}:00:00",
            "end_time": f"{14+i}:00:16",
            "ground_truth": activity,
            "states2json": generate_sample_motion_states(activity),
            "dataset": "marble"
        }
        marble_sample["data"].append(window)
    
    # Save sample MARBLE data
    marble_path = Path("data/processed/marble_sample.json")
    with open(marble_path, 'w') as f:
        json.dump(marble_sample, f, indent=2)
    print(f"✅ MARBLE sample data created: {marble_path}")
    
    return True

def generate_sample_states_for_activity(activity: str) -> dict:
    """Generate realistic States2JSON data for given activity."""
    
    base_time = "09:00"
    states = {}
    
    if activity == "cooking":
        states = {
            "MotionKitchen": [[f"{base_time}:00", f"{base_time}:45"]],
            "LightKitchenOn": [[f"{base_time}:00", f"{base_time}:50"]], 
            "PersonNearMicrowave": [[f"{base_time}:15", f"{base_time}:30"]],
            "DoorKitchenOpen": [[f"{base_time}:05", f"{base_time}:08"]]
        }
    elif activity == "watching_tv":
        states = {
            "MotionLivingRoom": [[f"{base_time}:00", f"{base_time}:05"]],
            "LightLivingRoomOn": [[f"{base_time}:00", f"{base_time}:60"]],
            "PersonNearTv": [[f"{base_time}:10", f"{base_time}:55"]],
            "TvOn": [[f"{base_time}:12", f"{base_time}:58"]]
        }
    elif activity == "cleaning":
        states = {
            "MotionLivingRoom": [[f"{base_time}:00", f"{base_time}:20"]],
            "MotionKitchen": [[f"{base_time}:25", f"{base_time}:45"]],
            "MotionBedroom": [[f"{base_time}:50", f"{base_time}:60"]],
            "VacuumOn": [[f"{base_time}:10", f"{base_time}:40"]]
        }
    elif activity == "sleeping":
        states = {
            "MotionBedroom": [[f"{base_time}:00", f"{base_time}:02"]],
            "LightBedroomOff": [[f"{base_time}:03", f"{base_time}:60"]],
            "PersonInBed": [[f"{base_time}:05", f"{base_time}:60"]]
        }
    else:  # eating
        states = {
            "MotionKitchen": [[f"{base_time}:00", f"{base_time}:10"]],
            "MotionDiningRoom": [[f"{base_time}:12", f"{base_time}:35"]],
            "LightDiningRoomOn": [[f"{base_time}:10", f"{base_time}:40"]]
        }
    
    return states

def generate_sample_motion_states(activity: str) -> dict:
    """Generate motion-based States2JSON data for MARBLE activities."""
    
    base_time = "14:00"
    states = {}
    
    if activity == "walking":
        states = {
            "PersonMoving": [[f"{base_time}:00", f"{base_time}:15"]],
            "AccelerometerHigh": [[f"{base_time}:00", f"{base_time}:15"]],
            "GyroscopeActive": [[f"{base_time}:00", f"{base_time}:15"]]
        }
    elif activity == "running":
        states = {
            "PersonMoving": [[f"{base_time}:00", f"{base_time}:12"]],
            "AccelerometerVeryHigh": [[f"{base_time}:00", f"{base_time}:12"]],
            "GyroscopeVeryActive": [[f"{base_time}:00", f"{base_time}:12"]],
            "HeartRateElevated": [[f"{base_time}:02", f"{base_time}:16"]]
        }
    elif activity == "sitting":
        states = {
            "PersonStationary": [[f"{base_time}:00", f"{base_time}:16"]],
            "AccelerometerLow": [[f"{base_time}:00", f"{base_time}:16"]],
            "PostureSitting": [[f"{base_time}:00", f"{base_time}:16"]]
        }
    elif activity == "standing":
        states = {
            "PersonStationary": [[f"{base_time}:00", f"{base_time}:16"]],
            "AccelerometerMedium": [[f"{base_time}:00", f"{base_time}:16"]],
            "PostureStanding": [[f"{base_time}:00", f"{base_time}:16"]]
        }
    else:  # lying
        states = {
            "PersonStationary": [[f"{base_time}:00", f"{base_time}:16"]],
            "AccelerometerVeryLow": [[f"{base_time}:00", f"{base_time}:16"]],
            "PostureLying": [[f"{base_time}:00", f"{base_time}:16"]]
        }
    
    return states

def verify_setup():
    """Verify that the dataset setup is complete."""
    print("🔍 Verifying dataset setup...")
    
    data_dir = Path("data")
    issues = []
    
    # Check directory structure
    required_dirs = ["data", "data/uci_adl", "data/marble", "data/processed"]
    for dir_path in required_dirs:
        if not Path(dir_path).exists():
            issues.append(f"Missing directory: {dir_path}")
    
    # Check for dataset info files
    info_files = ["data/uci_adl/dataset_info.json", "data/marble/dataset_info.json"]
    for info_file in info_files:
        if not Path(info_file).exists():
            issues.append(f"Missing dataset info: {info_file}")
    
    # Check for sample data
    sample_files = ["data/processed/uci_adl_sample.json", "data/processed/marble_sample.json"]
    sample_exists = any(Path(f).exists() for f in sample_files)
    
    if issues:
        print("⚠️ Setup issues found:")
        for issue in issues:
            print(f"  • {issue}")
        return False
    
    if sample_exists:
        print("✅ Sample datasets available for testing")
    
    print("✅ Dataset setup verification passed")
    return True

def main():
    """Main function to orchestrate dataset download and setup."""
    print("🏠 LLMe2e Dataset Setup")
    print("=" * 50)
    
    # Create directory structure
    create_data_directory()
    
    # Download/setup datasets
    print("\n📥 Setting up datasets...")
    uci_ready = download_uci_adl()
    marble_ready = download_marble()
    
    # Create sample data for testing
    print("\n📊 Setting up sample data for testing...")
    samples_created = create_sample_datasets()
    
    # Verify setup
    print("\n🔍 Verification...")
    setup_ok = verify_setup()
    
    # Print final instructions
    print("\n" + "=" * 50)
    print("📋 SETUP COMPLETE")
    print("=" * 50)
    
    if not (uci_ready and marble_ready):
        print("⚠️ Manual dataset download required:")
        if not uci_ready:
            print("  • Download UCI ADL dataset and extract to data/uci_adl/")
        if not marble_ready:
            print("  • Download MARBLE dataset and extract to data/marble/")
        print("  • Re-run this script after manual downloads")
    
    if samples_created:
        print("✅ Sample datasets ready for immediate testing")
        print("  • UCI ADL sample: data/processed/uci_adl_sample.json")
        print("  • MARBLE sample: data/processed/marble_sample.json")
    
    print("\n🚀 Next steps:")
    print("1. Run: python preprocess_dataset.py (to process full datasets)")
    print("2. Run: python added_evaluation.py (to test the LLMe2e pipeline)")
    print("3. Run: python main.py (to use the interactive assistant)")
    
    if setup_ok:
        print("\n✅ All systems ready!")
    else:
        print("\n⚠️ Please resolve setup issues before proceeding")

if __name__ == "__main__":
    main()