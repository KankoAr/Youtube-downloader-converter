#!/usr/bin/env python3
"""
Test script to verify that resources (styles and icons) are loading correctly
"""

import os
import sys
from app.utils import get_resource_path, get_icon_path

def test_resource_paths():
    """Test if resource paths are resolved correctly"""
    print("🧪 Testing resource paths...")
    print("=" * 50)
    
    # Test style.qss
    style_path = get_resource_path("style.qss")
    print(f"Style path: {style_path}")
    print(f"Style exists: {os.path.exists(style_path)}")
    
    # Test icons directory
    icons_dir = get_resource_path("icons")
    print(f"Icons directory: {icons_dir}")
    print(f"Icons directory exists: {os.path.exists(icons_dir)}")
    
    if os.path.exists(icons_dir):
        print("Icons found:")
        for icon in os.listdir(icons_dir):
            if icon.endswith(('.svg', '.png', '.ico')):
                icon_path = get_icon_path(icon)
                print(f"  - {icon}: {os.path.exists(icon_path)}")
    
    # Test specific icon
    test_icon = get_icon_path("download-white-svg.svg")
    print(f"Test icon path: {test_icon}")
    print(f"Test icon exists: {os.path.exists(test_icon)}")
    
    print("=" * 50)
    
    # Check if we're running from PyInstaller
    try:
        meipass = sys._MEIPASS
        print(f"Running from PyInstaller: {meipass}")
        print(f"MEIPASS contents: {os.listdir(meipass) if os.path.exists(meipass) else 'Not found'}")
    except AttributeError:
        print("Running from development environment")
    
    # Check current working directory
    print(f"Current working directory: {os.getcwd()}")
    print(f"Current directory contents: {os.listdir('.')}")

if __name__ == "__main__":
    test_resource_paths()
