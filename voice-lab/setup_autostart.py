"""
Windows Auto-Start Setup
Registers or unregisters the Voice Assistant to launch automatically upon Windows login.
"""
import os
import sys
import argparse

STARTUP_DIR = os.path.expandvars(r"%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup")
VBS_PATH = os.path.join(STARTUP_DIR, "StartAutonomousAssistant.vbs")
ASSISTANT_BAT = os.path.abspath(os.path.join(os.path.dirname(__file__), "start_assistant.bat"))

def enable_autostart(minimized: bool = True):
    """Creates a startup VBS script to run the assistant automatically on boot."""
    win_style = 7 if minimized else 1
    bat_escaped = ASSISTANT_BAT.replace('"', '""')
    vbs_content = (
        "' Autonomous Voice Assistant Startup Runner\n"
        "Set WshShell = CreateObject(\"WScript.Shell\")\n"
        f"WshShell.CurrentDirectory = \"{os.path.dirname(ASSISTANT_BAT)}\"\n"
        f"WshShell.Run chr(34) & \"{bat_escaped}\" & chr(34), {win_style}, False\n"
    )
    try:
        os.makedirs(STARTUP_DIR, exist_ok=True)
        with open(VBS_PATH, "w", encoding="utf-8") as f:
            f.write(vbs_content)
        print(f"[+] SUCCESS: Auto-start enabled on Windows login!")
        print(f"    Startup shortcut created at:\n    {VBS_PATH}")
        print(f"    Target script:\n    {ASSISTANT_BAT}")
        return True
    except Exception as e:
        print(f"[-] Failed to enable auto-start: {e}")
        return False

def disable_autostart():
    """Removes the startup script."""
    if os.path.exists(VBS_PATH):
        try:
            os.remove(VBS_PATH)
            print("[+] SUCCESS: Auto-start disabled. Assistant will no longer launch on boot.")
            return True
        except Exception as e:
            print(f"[-] Failed to remove startup script: {e}")
            return False
    else:
        print("[*] Auto-start is already disabled.")
        return True

def check_status():
    """Checks whether auto-start is currently active."""
    if os.path.exists(VBS_PATH):
        print(f"[+] Auto-start is currently ENABLED. (Script: {VBS_PATH})")
    else:
        print("[-] Auto-start is currently DISABLED.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Configure Windows auto-start on boot.")
    parser.add_argument("--enable", action="store_true", help="Enable auto-start on login")
    parser.add_argument("--disable", action="store_true", help="Disable auto-start on login")
    parser.add_argument("--status", action="store_true", help="Check auto-start status")
    parser.add_argument("--visible", action="store_true", help="Launch in normal visible window instead of minimized")

    args = parser.parse_args()

    if args.enable:
        enable_autostart(minimized=not args.visible)
    elif args.disable:
        disable_autostart()
    else:
        check_status()
