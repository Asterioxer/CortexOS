"""CLI interface for CortexOS background daemon and system boot autostart management.

Usage:
  python -m cortex.startup status
  python -m cortex.startup start [--host HOST] [--port PORT]
  python -m cortex.startup stop
  python -m cortex.startup restart
  python -m cortex.startup install [--host HOST] [--port PORT]
  python -m cortex.startup uninstall
  python -m cortex.startup network
"""

import sys
import argparse
import json
from cortex.startup.service_manager import get_service_manager


if sys.platform == "win32":
    # Ensure stdout handles UTF-8 / unicode symbols gracefully on Windows
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def main():
    parser = argparse.ArgumentParser(
        prog="python -m cortex.startup",
        description="CortexOS Autonomous System Startup & Background Daemon Manager"
    )
    parser.add_argument(
        "action",
        choices=["status", "start", "stop", "restart", "install", "enable", "uninstall", "disable", "network", "ip"],
        help="Action to perform"
    )
    parser.add_argument("--host", default="0.0.0.0", help="Host address to bind (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind (default: 8000)")
    parser.add_argument("--json", action="store_true", help="Output raw JSON instead of formatted text")

    args = parser.parse_args()
    mgr = get_service_manager()

    if args.action == "status":
        st = mgr.status(port=args.port)
        if args.json:
            print(json.dumps(st, indent=2))
        else:
            net = st["network"]
            auto = st["autostart"]
            print("=" * 68)
            print("🧠 CORTEX-OS // AUTONOMOUS SYSTEM DAEMON STATUS")
            print("=" * 68)
            print(f"  Operating System:    {st['platform'].upper()} ({net['platform']})")
            print(f"  Daemon State:        {'🟢 RUNNING (PID ' + str(st['pid']) + ')' if st['running'] else '🔴 STOPPED'}")
            if st["running"]:
                print(f"  Memory / CPU:        {st['memory_mb']} MB / {st['cpu_percent']}%")
                print(f"  Uptime:              {st['uptime_seconds']}s")
            print(f"  Boot Autostart:      {'✅ ENABLED (' + auto['method'] + ')' if auto['enabled'] else '❌ DISABLED'}")
            print(f"  Local Loopback:      {net['local_url']}")
            print(f"  Network/LAN Access:  {net['network_url']} (Accessible from phone/devices)")
            print(f"  All Host IPs:        {', '.join(net['all_ips'])}")
            print(f"  Daemon Executable:   {st['executable']}")
            print(f"  Log File:            {st['log_file']}")
            print("=" * 68)

    elif args.action in ["start"]:
        print(f"[*] Starting CortexOS background daemon on {args.host}:{args.port}...")
        res = mgr.start_daemon(host=args.host, port=args.port)
        if args.json:
            print(json.dumps(res, indent=2))
        else:
            if res.get("status") in ["SUCCESS", "ALREADY_RUNNING"]:
                print(f"[✓] {res.get('message')}")
                print(f"    Local URL:   {res.get('local_url')}")
                print(f"    Network URL: {res.get('network_url')}")
            else:
                print(f"[!] {res.get('message', 'Failed to start daemon')}")

    elif args.action in ["stop"]:
        print("[*] Halting CortexOS background daemon...")
        res = mgr.stop_daemon(port=args.port)
        if args.json:
            print(json.dumps(res, indent=2))
        else:
            print(f"[✓] {res.get('message')}")

    elif args.action in ["restart"]:
        print("[*] Restarting CortexOS daemon...")
        mgr.stop_daemon(port=args.port)
        res = mgr.start_daemon(host=args.host, port=args.port)
        if args.json:
            print(json.dumps(res, indent=2))
        else:
            print(f"[✓] {res.get('message')}")
            print(f"    Local URL:   {res.get('local_url')}")
            print(f"    Network URL: {res.get('network_url')}")

    elif args.action in ["install", "enable"]:
        print(f"[*] Registering CortexOS for automatic system startup on {st_platform()} boot...")
        res = mgr.install_autostart(host=args.host, port=args.port)
        if args.json:
            print(json.dumps(res, indent=2))
        else:
            print(f"[✓] {res.get('message')}")

    elif args.action in ["uninstall", "disable"]:
        print(f"[*] Removing CortexOS autostart from {st_platform()}...")
        res = mgr.uninstall_autostart()
        if args.json:
            print(json.dumps(res, indent=2))
        else:
            print(f"[✓] {res.get('message')}")

    elif args.action in ["network", "ip"]:
        net = mgr.get_network_info(port=args.port)
        if args.json:
            print(json.dumps(net, indent=2))
        else:
            print(f"Hostname:        {net['hostname']}")
            print(f"Primary LAN IP:  {net['primary_ip']}")
            print(f"Local Access:    {net['local_url']}")
            print(f"Network Access:  {net['network_url']}")
            print(f"Interfaces:      {', '.join(net['all_ips'])}")


def st_platform() -> str:
    import platform
    return platform.system()


if __name__ == "__main__":
    main()
