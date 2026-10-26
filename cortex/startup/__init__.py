"""CortexOS System Startup & Autonomous Daemon Management Subsystem.

Provides cross-platform background daemon management, boot-time system startup,
and seamless LAN/network accessibility across Windows, Linux, and macOS.
"""

from cortex.startup.service_manager import ServiceManager, get_service_manager

__all__ = ["ServiceManager", "get_service_manager"]
