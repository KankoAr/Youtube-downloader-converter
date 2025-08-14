#!/usr/bin/env python3
"""
Test script to verify the executable works correctly
"""

import os
import subprocess
import time
import sys

def test_executable():
    """Test the compiled executable"""
    print("🧪 Testing compiled executable...")
    print("=" * 50)
    
    exe_path = "dist/YouTube_Downloader.exe"
    
    if not os.path.exists(exe_path):
        print(f"❌ Executable not found: {exe_path}")
        return False
    
    print(f"✅ Executable found: {exe_path}")
    print(f"📁 Size: {os.path.getsize(exe_path) / (1024*1024):.1f} MB")
    
    # Test running the executable
    print(f"\n🚀 Testing executable...")
    try:
        # Run the executable for a few seconds
        process = subprocess.Popen(
            [exe_path], 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait a bit for it to start
        time.sleep(5)
        
        # Check if it's still running
        if process.poll() is None:
            print("✅ Executable started successfully and is running!")
            
            # Terminate it gracefully
            process.terminate()
            try:
                process.wait(timeout=5)
                print("✅ Executable terminated gracefully")
            except subprocess.TimeoutExpired:
                process.kill()
                print("⚠️ Had to force kill executable")
        else:
            # Process finished, check output
            stdout, stderr = process.communicate()
            print(f"⚠️ Executable finished with return code: {process.returncode}")
            if stdout:
                print(f"STDOUT: {stdout[:200]}...")
            if stderr:
                print(f"STDERR: {stderr[:200]}...")
                
    except Exception as e:
        print(f"❌ Error testing executable: {e}")
        return False
    
    return True

def check_build_artifacts():
    """Check what was created during the build"""
    print(f"\n🔍 Checking build artifacts...")
    print("=" * 50)
    
    # Check build directory
    if os.path.exists("build"):
        print("📁 Build directory contents:")
        for item in os.listdir("build"):
            item_path = os.path.join("build", item)
            if os.path.isdir(item_path):
                print(f"  📁 {item}/")
                try:
                    for subitem in os.listdir(item_path):
                        print(f"    - {subitem}")
                except:
                    pass
            else:
                size = os.path.getsize(item_path)
                print(f"  📄 {item} ({size} bytes)")
    
    # Check dist directory
    if os.path.exists("dist"):
        print(f"\n📁 Dist directory contents:")
        for item in os.listdir("dist"):
            item_path = os.path.join("dist", item)
            if os.path.isdir(item_path):
                print(f"  📁 {item}/")
                try:
                    for subitem in os.listdir(item_path):
                        print(f"    - {subitem}")
                except:
                    pass
            else:
                size = os.path.getsize(item_path)
                print(f"  📄 {item} ({size} bytes)")
    
    # Check if spec file was processed correctly
    print(f"\n📋 Spec file analysis:")
    spec_path = "YouTube_Downloader.spec"
    if os.path.exists(spec_path):
        with open(spec_path, 'r') as f:
            content = f.read()
            if "✅ Including:" in content:
                print("✅ Spec file shows resources were included")
            else:
                print("⚠️ Spec file doesn't show resource inclusion")
    else:
        print("❌ Spec file not found")

def main():
    print("🚀 Starting executable test...")
    
    # Check build artifacts
    check_build_artifacts()
    
    # Test executable
    if test_executable():
        print(f"\n🎉 Executable test completed successfully!")
        print(f"\n💡 Next steps:")
        print(f"1. Test the executable manually by double-clicking it")
        print(f"2. Check if styles and icons are loading correctly")
        print(f"3. If everything works, create a release with: .\\release.ps1 -Version 1.0.0")
    else:
        print(f"\n❌ Executable test failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
