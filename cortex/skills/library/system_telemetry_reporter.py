"""
Integrity Hash: 7a8f9023b81c
Description: Somatosensory system telemetry reporter capturing CPU, RAM, GPU, and active audio playback.
"""
import asyncio
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

from cortex.embodiment.system_somatosensory import SystemSomatosensory

async def run_report():
    somato = SystemSomatosensory()
    hw = somato.get_hardware_telemetry()
    apps = somato.get_user_applications(top_n=6)
    media = await somato.get_active_media_playback()

    cpu = hw.get("cpu", {})
    ram = hw.get("ram", {})
    disk = hw.get("disk_c", {})
    batt = hw.get("battery", {})
    gpu = hw.get("gpu", {})

    print("=== LIVE SOMATOSENSORY TELEMETRY REPORT ===")
    print(f"Platform: {hw.get('os')} (User: {hw.get('user')})")
    print(f"CPU Load: {cpu.get('percent')}% across {cpu.get('cores_logical')} logical threads")
    print(f"Memory:   {ram.get('used_gb')} GB / {ram.get('total_gb')} GB ({ram.get('percent')}%)")
    print(f"Storage:  {disk.get('used_gb')} GB / {disk.get('total_gb')} GB ({disk.get('percent')}%)")
    print(f"Power:    {batt.get('percent')}% (AC Connected: {batt.get('plugged_in')})")
    if gpu and gpu.get("name"):
        print(f"GPU:      {gpu.get('name')} ({gpu.get('memory_used_mb')}MB/{gpu.get('memory_total_mb')}MB, {gpu.get('temperature_c')}C)")
    if media and media.get("title"):
        print(f"Audio:    '{media.get('title')}' by {media.get('artist')} [{media.get('source_app')}]")
    if apps:
        app_names = [a.get("name") for a in apps]
        print(f"Active GUI Applications: {', '.join(app_names)}")
    return 0

def main():
    return asyncio.run(run_report())

if __name__ == "__main__":
    sys.exit(main())
