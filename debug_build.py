#!/usr/bin/env python3
"""
Debug script for PyInstaller build issues
"""

import os
import sys
import subprocess
import shutil

def debug_build():
    """Debug the PyInstaller build process"""
    print("🐛 PyInstaller Debug Mode")
    print("=" * 50)
    
    # Check current directory
    print(f"Current directory: {os.getcwd()}")
    print(f"Files in current directory:")
    for item in os.listdir('.'):
        print(f"  - {item}")
    
    # Check if spec file exists
    spec_file = "YouTube_Downloader.spec"
    if os.path.exists(spec_file):
        print(f"\n✅ Spec file found: {spec_file}")
        with open(spec_file, 'r') as f:
            content = f.read()
            print(f"Spec file size: {len(content)} characters")
    else:
        print(f"\n❌ Spec file not found: {spec_file}")
        return False
    
    # Check resources
    print(f"\n🔍 Checking resources:")
    resources = [
        ('style.qss', 'Stylesheet'),
        ('icons', 'Icons directory'),
        ('main.py', 'Main script'),
        ('app', 'App package')
    ]
    
    for resource, description in resources:
        if os.path.exists(resource):
            if os.path.isdir(resource):
                files = os.listdir(resource)
                print(f"  ✅ {description}: {resource} ({len(files)} files)")
                if resource == 'icons':
                    for icon in files:
                        print(f"    - {icon}")
            else:
                size = os.path.getsize(resource)
                print(f"  ✅ {description}: {resource} ({size} bytes)")
        else:
            print(f"  ❌ {description}: {resource} (MISSING)")
    
    # Try to run PyInstaller with debug info
    print(f"\n🔨 Running PyInstaller with debug info...")
    try:
        cmd = [
            sys.executable, '-m', 'PyInstaller',
            '--clean',
            '--log-level=DEBUG',
            '--distpath=dist_debug',
            '--workpath=build_debug',
            '--specpath=.',
            'YouTube_Downloader.spec'
        ]
        
        print(f"Command: {' '.join(cmd)}")
        
        # Run PyInstaller
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        print(f"\nExit code: {result.returncode}")
        
        if result.stdout:
            print(f"\nSTDOUT:")
            print(result.stdout)
        
        if result.stderr:
            print(f"\nSTDERR:")
            print(result.stderr)
        
        if result.returncode == 0:
            print(f"\n✅ Build completed successfully!")
            
            # Check output
            if os.path.exists('dist_debug'):
                print(f"Debug dist contents:")
                for item in os.listdir('dist_debug'):
                    item_path = os.path.join('dist_debug', item)
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
            
            # Clean up debug directories
            if os.path.exists('dist_debug'):
                shutil.rmtree('dist_debug')
            if os.path.exists('build_debug'):
                shutil.rmtree('build_debug')
                
        else:
            print(f"\n❌ Build failed!")
            return False
            
    except Exception as e:
        print(f"\n❌ Error running PyInstaller: {e}")
        return False
    
    return True

def main():
    print("🚀 Starting PyInstaller debug...")
    
    if debug_build():
        print("\n🎉 Debug completed successfully!")
        print("\n💡 If you still have issues, check:")
        print("1. All resource files exist")
        print("2. PyInstaller is up to date")
        print("3. No antivirus blocking the build")
        print("4. Sufficient disk space")
    else:
        print("\n❌ Debug failed. Check the output above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
