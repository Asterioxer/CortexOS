import os
import sys
import platform
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from cortex.startup.service_manager import ServiceManager, get_service_manager
from cortex.server import app

client = TestClient(app)


def test_service_manager_initialization():
    mgr = ServiceManager()
    assert mgr.workspace_root.exists()
    assert mgr.server_script.name == "server.py"
    assert mgr.os_type in ["windows", "linux", "darwin"]
    assert mgr.cortex_dir.name == ".cortex"


def test_network_and_lan_ip_discovery():
    mgr = ServiceManager()
    lan_ip = mgr.get_primary_lan_ip()
    assert isinstance(lan_ip, str)
    assert len(lan_ip.split(".")) == 4

    net_info = mgr.get_network_info(port=8000)
    assert "hostname" in net_info
    assert "primary_ip" in net_info
    assert "local_url" in net_info
    assert "network_url" in net_info
    assert net_info["local_url"] == "http://127.0.0.1:8000"
    assert f":8000" in net_info["network_url"]


def test_status_snapshot():
    mgr = ServiceManager()
    status = mgr.status(port=8000)
    assert "running" in status
    assert "autostart" in status
    assert "network" in status
    assert "platform" in status
    assert "executable" in status
    assert "script" in status
    assert isinstance(status["autostart"], dict)
    assert "enabled" in status["autostart"]


def test_linux_systemd_and_xdg_templates(tmp_path):
    mgr = ServiceManager(workspace_root=tmp_path)
    mgr.os_type = "linux"

    # Mock user home directory
    with patch.object(Path, "home", return_value=tmp_path):
        res = mgr._linux_install_autostart(host="0.0.0.0", port=8000)
        assert res["status"] == "SUCCESS"
        assert res["platform"] == "linux"

        # Verify systemd service unit file content
        service_file = tmp_path / ".config" / "systemd" / "user" / "cortexos.service"
        assert service_file.exists()
        content = service_file.read_text(encoding="utf-8")
        assert "[Unit]" in content
        assert "Description=CortexOS" in content
        assert "CORTEX_HOST=0.0.0.0" in content
        assert "CORTEX_PORT=8000" in content
        assert "[Install]" in content
        assert "WantedBy=default.target" in content

        # Verify XDG autostart desktop entry
        desktop_file = tmp_path / ".config" / "autostart" / "cortexos.desktop"
        assert desktop_file.exists()
        desktop_content = desktop_file.read_text(encoding="utf-8")
        assert "[Desktop Entry]" in desktop_content
        assert "Type=Application" in desktop_content
        assert "Name=CortexOS" in desktop_content

        # Verify uninstall
        uninst = mgr._linux_uninstall_autostart()
        assert uninst["status"] == "SUCCESS"
        assert not service_file.exists()
        assert not desktop_file.exists()


def test_darwin_launchd_plist_template(tmp_path):
    mgr = ServiceManager(workspace_root=tmp_path)
    mgr.os_type = "darwin"

    with patch.object(Path, "home", return_value=tmp_path):
        res = mgr._darwin_install_autostart(host="0.0.0.0", port=8000)
        assert res["status"] == "SUCCESS"
        assert res["platform"] == "darwin"

        plist_file = tmp_path / "Library" / "LaunchAgents" / f"{mgr.SERVICE_LABEL}.plist"
        assert plist_file.exists()
        plist_content = plist_file.read_text(encoding="utf-8")
        assert "<key>Label</key>" in plist_content
        assert f"<string>{mgr.SERVICE_LABEL}</string>" in plist_content
        assert "<key>RunAtLoad</key>" in plist_content
        assert "<true/>" in plist_content
        assert "<key>CORTEX_PORT</key>" in plist_content
        assert "<string>8000</string>" in plist_content

        # Verify uninstall
        uninst = mgr._darwin_uninstall_autostart()
        assert uninst["status"] == "SUCCESS"
        assert not plist_file.exists()


def test_windows_autostart_logic(tmp_path):
    mgr = ServiceManager(workspace_root=tmp_path)
    mgr.os_type = "windows"

    # Test startup folder VBScript generation
    fake_appdata = tmp_path / "AppData" / "Roaming"
    fake_appdata.mkdir(parents=True, exist_ok=True)

    with patch.dict(os.environ, {"APPDATA": str(fake_appdata)}), \
         patch("cortex.startup.service_manager.winreg", None):
        res = mgr._windows_install_autostart(host="0.0.0.0", port=8000)
        assert res["status"] == "SUCCESS"
        assert "startup_folder_vbs" in res["methods"]

        vbs_path = fake_appdata / r"Microsoft\Windows\Start Menu\Programs\Startup\cortexos_daemon.vbs"
        assert vbs_path.exists()
        vbs_code = vbs_path.read_text(encoding="utf-8")
        assert "CreateObject" in vbs_code
        assert "CORTEX_HOST" in vbs_code
        assert "CORTEX_PORT" in vbs_code

        # Cleanup via uninstall
        uninst_res = mgr._windows_uninstall_autostart()
        assert uninst_res["status"] == "SUCCESS"
        assert not vbs_path.exists()


def test_api_system_daemon():
    res = client.get("/api/system/daemon")
    assert res.status_code == 200
    data = res.json()
    assert "platform" in data
    assert "autostart" in data
    assert "network" in data
    assert "executable" in data


def test_api_system_network():
    res = client.get("/api/system/network")
    assert res.status_code == 200
    data = res.json()
    assert "primary_ip" in data
    assert "local_url" in data
    assert "network_url" in data
    assert data["local_url"].startswith("http://127.0.0.1")


def test_api_execution_daemons_includes_system_daemon():
    res = client.get("/api/execution/daemons")
    assert res.status_code == 200
    data = res.json()
    assert "uvicorn_server" in data
    assert "ambient_worker" in data
    assert "stall_breaker" in data
    assert "sleep_daemon" in data
    assert "system_daemon" in data
    assert "platform" in data["system_daemon"]
    assert "network" in data["system_daemon"]


def test_dashboard_ui_elements():
    res = client.get("/")
    assert res.status_code == 200
    html = res.text
    # Header ticker contains LAN network monitor
    assert 'id="ticker-network"' in html
    assert 'id="net-ticker-text"' in html
    # Execution pane contains 5 supervisors and cross-platform daemon card
    assert "5 Autonomous Supervisors & Daemons" in html
    assert "System Boot & LAN Daemon" in html
    assert "btn-autostart-toggle" in html
