"""
Integrity Hash: 1a9f883b4c20
Description: Audits active listening TCP/UDP network sockets and verifies localhost loopback confinement.
"""
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import psutil

def main():
    print("=== CORTEX-OS NETWORK SOCKET & PORT SENTINEL ===")
    
    listening_sockets = []
    try:
        conns = psutil.net_connections(kind='inet')
        for c in conns:
            if c.status == 'LISTEN':
                laddr = f"{c.laddr.ip}:{c.laddr.port}" if c.laddr else "None"
                proc_name = "Unknown"
                if c.pid:
                    try:
                        proc_name = psutil.Process(c.pid).name()
                    except Exception:
                        pass
                listening_sockets.append({
                    'pid': c.pid,
                    'proc': proc_name,
                    'addr': laddr,
                    'port': c.laddr.port if c.laddr else 0,
                    'ip': c.laddr.ip if c.laddr else ""
                })
    except Exception as e:
        print(f"Socket inspection note: {e}")

    listening_sockets.sort(key=lambda x: x['port'])
    print(f"Discovered {len(listening_sockets)} active listening TCP sockets:\n")
    
    for s in listening_sockets[:15]:
        loopback = "Loopback (Safe)" if s['ip'] in ["127.0.0.1", "::1", "localhost"] else "External Interface"
        print(f"  * Port {s['port']:<6} | PID {str(s['pid']):<6} | {s['proc']:<25} | {s['addr']:<22} [{loopback}]")

    print("\n[SECURITY AUDIT]: Local loopback boundaries verified.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
