import os
import sys


def get_resource_path(relative_path: str) -> str:
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        # Development environment
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)


def get_icon_path(icon_name: str) -> str:
    """Get path to an icon file"""
    return get_resource_path(os.path.join("icons", icon_name))
