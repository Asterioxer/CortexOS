"""
Integrity Hash: 9c2a1e843f01
Description: Analyzes active system processes, detects CPU/RAM resource hogs, and identifies optimization candidates.
"""
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import psutil

def main():
    print("=== CORTEX-OS PROCESS RESOURCE OPTIMIZER ===")
    
    vm = psutil.virtual_memory()
    total_gb = round(vm.total / (1024**3), 1)
    used_gb = round(vm.used / (1024**3), 1)
    print(f"Physical Memory Pressure: {used_gb} GB / {total_gb} GB ({vm.percent}%)")
    
    # Analyze processes
    heavy_procs = []
    total_scanned = 0
    for p in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'status']):
        try:
            total_scanned += 1
            info = p.info
            mem_pct = info.get('memory_percent') or 0.0
            cpu_pct = info.get('cpu_percent') or 0.0
            if mem_pct > 1.5 or cpu_pct > 3.0:
                heavy_procs.append({
                    'pid': info['pid'],
                    'name': info['name'],
                    'mem_pct': round(mem_pct, 2),
                    'cpu_pct': round(cpu_pct, 1),
                    'status': info.get('status', 'running')
                })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass

    heavy_procs.sort(key=lambda x: x['mem_pct'], reverse=True)
    
    print(f"\nScanned {total_scanned} active system processes.")
    print(f"Identified {len(heavy_procs)} processes with elevated resource footprint:\n")
    
    for hp in heavy_procs[:10]:
        print(f"  * PID {hp['pid']:<6} | {hp['name']:<28} | RAM: {hp['mem_pct']:>5.2f}% | CPU: {hp['cpu_pct']:>5.1f}% | Status: {hp['status']}")

    if vm.percent > 85.0:
        print("\n[RECOMMENDATION]: High memory pressure detected (>85%). Consider terminating idle browser renderer tabs.")
    else:
        print("\n[RECOMMENDATION]: Memory load is within optimal operating parameters.")
        
    return 0

if __name__ == "__main__":
    sys.exit(main())
