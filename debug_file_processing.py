import os
import glob
from pathlib import Path

def debug_file_issues():
    """Debug why files aren't being processed"""
    
    # Test different possible paths
    possible_paths = [
        "~/Downloads/chapters",
        os.path.expanduser("~/Downloads/chapters"),
        "./text_files",
        "/Volumes/data/code/graphiti-config/text_files"
    ]
    
    print("🔍 Debugging file processing issues...")
    print("=" * 50)
    
    for path in possible_paths:
        expanded_path = os.path.expanduser(path)
        print(f"\n📁 Checking path: {path}")
        print(f"   Expanded to: {expanded_path}")
        print(f"   Exists: {os.path.exists(expanded_path)}")
        
        if os.path.exists(expanded_path):
            txt_files = glob.glob(os.path.join(expanded_path, "*.txt"))
            print(f"   .txt files found: {len(txt_files)}")
            
            if txt_files:
                print("   Sample files:")
                for i, file_path in enumerate(sorted(txt_files)[:3]):
                    filename = Path(file_path).name
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        size = len(content)
                        print(f"     {i+1}. {filename} ({size} characters)")
                        
                        if size < 100:
                            print(f"        ⚠️  File is very short (would be skipped)")
                        else:
                            print(f"        ✅ File size OK")
                            
                    except Exception as e:
                        print(f"     {i+1}. {filename} - Error reading: {e}")
                break
        else:
            print(f"   ❌ Path does not exist")
    
    # Also check what path was actually used in the last run
    print(f"\n🔍 Manual file check:")
    manual_path = input("Enter the exact path you used when running the script: ").strip()
    if manual_path:
        expanded = os.path.expanduser(manual_path)
        print(f"Expanded path: {expanded}")
        print(f"Exists: {os.path.exists(expanded)}")
        if os.path.exists(expanded):
            files = glob.glob(os.path.join(expanded, "*.txt"))
            print(f"Files found: {len(files)}")
            for f in files[:3]:
                print(f"  - {Path(f).name}")

if __name__ == "__main__":
    debug_file_issues()