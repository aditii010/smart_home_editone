# file_checker.py - Run this to check and fix your file structure

import os
import shutil
from pathlib import Path

def check_file_structure():
    """Check current file structure and identify issues"""
    print("🔍 Checking file structure...")
    print("=" * 50)
    
    current_dir = Path.cwd()
    print(f"📁 Current directory: {current_dir}")
    print()
    
    # List all Python files
    py_files = list(current_dir.glob("*.py"))
    print("🐍 Python files found:")
    for file in py_files:
        print(f"   {file.name} ({file.stat().st_size} bytes)")
    print()
    
    # Check for duplicates
    file_names = [f.name for f in py_files]
    duplicates = []
    seen = set()
    for name in file_names:
        if name in seen:
            duplicates.append(name)
        seen.add(name)
    
    if duplicates:
        print("⚠️  Duplicate files found:")
        for dup in duplicates:
            print(f"   {dup}")
        print()
    
    # Check for subdirectories
    subdirs = [d for d in current_dir.iterdir() if d.is_dir()]
    print("📂 Subdirectories:")
    for subdir in subdirs:
        print(f"   {subdir.name}/")
        # Check for Python files in subdirs
        sub_py_files = list(subdir.glob("*.py"))
        for sub_file in sub_py_files:
            print(f"      {sub_file.name}")
    print()
    
    return current_dir, py_files, subdirs

def fix_file_structure():
    """Fix common file structure issues"""
    current_dir, py_files, subdirs = check_file_structure()
    
    print("🔧 Attempting to fix file structure...")
    print("=" * 50)
    
    # Check if we're in a nested directory
    if current_dir.name == "smart-home-agent-ai" and current_dir.parent.name == "smart-home-agent-ai":
        print("🔍 Detected nested directory structure")
        parent_dir = current_dir.parent
        
        # List files in parent directory
        parent_py_files = list(parent_dir.glob("*.py"))
        if parent_py_files:
            print(f"📁 Found Python files in parent directory: {parent_dir}")
            for file in parent_py_files:
                print(f"   {file.name}")
            
            response = input("\n❓ Move files from parent directory down? (y/n): ").lower()
            if response == 'y':
                for file in parent_py_files:
                    dest = current_dir / file.name
                    if not dest.exists():
                        shutil.move(str(file), str(dest))
                        print(f"✅ Moved {file.name} to current directory")
                    else:
                        print(f"⚠️  {file.name} already exists in current directory")
    
    # Remove duplicate files
    duplicates = {}
    for file in py_files:
        name = file.name
        if name in duplicates:
            # Keep the newer file
            if file.stat().st_mtime > duplicates[name].stat().st_mtime:
                print(f"🗑️  Removing older duplicate: {duplicates[name].name}")
                duplicates[name].unlink()
                duplicates[name] = file
            else:
                print(f"🗑️  Removing older duplicate: {file.name}")
                file.unlink()
        else:
            duplicates[name] = file
    
    # Create scripts directory if it doesn't exist
    scripts_dir = current_dir / "scripts"
    if not scripts_dir.exists():
        print("📁 Creating scripts directory...")
        scripts_dir.mkdir()
        
        # Create __init__.py
        (scripts_dir / "__init__.py").write_text("# Scripts package\n")
        print("✅ Created scripts/__init__.py")
    
    # Create docs directory if it doesn't exist
    docs_dir = current_dir / "docs"
    if not docs_dir.exists():
        print("📁 Creating docs directory...")
        docs_dir.mkdir()
        print("✅ Created docs directory")
    
    print("\n✅ File structure fixes completed!")
    
    # Show final structure
    print("\n📊 Final project structure:")
    show_project_structure(current_dir)

def show_project_structure(base_dir):
    """Show the project structure in a tree format"""
    def print_tree(directory, prefix="", max_depth=3, current_depth=0):
        if current_depth >= max_depth:
            return
        
        items = sorted(directory.iterdir(), key=lambda x: (x.is_file(), x.name))
        for i, item in enumerate(items):
            is_last = i == len(items) - 1
            
            # Print current item
            connector = "└── " if is_last else "├── "
            print(f"{prefix}{connector}{item.name}{'/' if item.is_dir() else ''}")
            
            # Recurse into directories
            if item.is_dir() and current_depth < max_depth - 1:
                extension = "    " if is_last else "│   "
                print_tree(item, prefix + extension, max_depth, current_depth + 1)
    
    print(f"{base_dir.name}/")
    print_tree(base_dir)

def create_missing_files():
    """Create any missing essential files"""
    current_dir = Path.cwd()
    
    # Check for main.py
    main_py = current_dir / "main.py"
    if not main_py.exists():
        print("❌ main.py not found")
        create_main = input("❓ Create main.py? (y/n): ").lower()
        if create_main == 'y':
            # You can copy the content from the artifact we created earlier
            print("💡 Please copy the main.py content from the previous artifact")
    else:
        print("✅ main.py found")
    
    # Check for rag_engine.py
    rag_engine_py = current_dir / "rag_engine.py"
    if not rag_engine_py.exists():
        print("❌ rag_engine.py not found")
        create_rag = input("❓ Create rag_engine.py? (y/n): ").lower()
        if create_rag == 'y':
            print("💡 Please copy the rag_engine.py content from the previous artifact")
    else:
        print("✅ rag_engine.py found")
    
    # Check for scripts
    scripts_dir = current_dir / "scripts"
    required_scripts = ["llm_interface.py", "smart_home_api.py"]
    
    for script in required_scripts:
        script_path = scripts_dir / script
        if not script_path.exists():
            print(f"❌ scripts/{script} not found")
        else:
            print(f"✅ scripts/{script} found")

if __name__ == "__main__":
    print("🏠 Smart Home Agent - File Structure Checker")
    print("=" * 60)
    
    try:
        fix_file_structure()
        print("\n" + "=" * 60)
        create_missing_files()
        
        print("\n🎉 File structure check completed!")
        print("\n💡 Next steps:")
        print("   1. Run: python create_scripts.py  (if scripts are missing)")
        print("   2. Run: python main.py  (to start the application)")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()