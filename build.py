#!/usr/bin/env python3
"""
Build script for YouTube Downloader
Builds the executable using PyInstaller
"""

import os
import shutil
import subprocess
import sys

def clean_build():
    """Clean previous build artifacts"""
    dirs_to_clean = ['build', 'dist', '__pycache__']
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"Cleaned {dir_name}")

def verify_resources():
    """Verify that all required resources exist"""
    print("🔍 Verifying resources...")
    
    required_files = [
        'style.qss',
        'icons/download-white-svg.svg',
        'icons/converter-white.svg',
        'icons/configuration-white.svg'
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
            print(f"❌ Missing: {file_path}")
        else:
            print(f"✅ Found: {file_path}")
    
    if missing_files:
        print(f"\n❌ Missing {len(missing_files)} required files!")
        return False
    
    print("✅ All resources verified!")
    return True

def build_executable():
    """Build the executable using PyInstaller"""
    try:
        # Verify resources first
        if not verify_resources():
            print("❌ Resource verification failed. Cannot proceed with build.")
            return False
        
        # Check if PyInstaller is installed
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'pyinstaller'], check=True)
        
        # Build using the spec file
        cmd = [sys.executable, '-m', 'PyInstaller', '--clean', 'YouTube_Downloader.spec']
        subprocess.run(cmd, check=True)
        
        print("✅ Build completed successfully!")
        print(f"Executable location: {os.path.abspath('dist/YouTube_Downloader.exe')}")
        
        # Test the executable
        print("\n🧪 Testing executable...")
        test_cmd = [os.path.abspath('dist/YouTube_Downloader.exe')]
        try:
            # Run for a few seconds to test
            process = subprocess.Popen(test_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            import time
            time.sleep(3)
            process.terminate()
            print("✅ Executable test completed!")
        except Exception as e:
            print(f"⚠️ Executable test failed: {e}")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Build failed: {e}")
        return False
    
    return True

def main():
    print("🚀 Starting build process...")
    
    # Clean previous builds
    clean_build()
    
    # Build executable
    if build_executable():
        print("\n🎉 Build completed! You can find the executable in the 'dist' folder.")
        print("\nTo create a release:")
        print("1. git add .")
        print("2. git commit -m 'Release v1.0.0'")
        print("3. git tag v1.0.0")
        print("4. git push origin main --tags")
    else:
        print("\n❌ Build failed. Please check the error messages above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
