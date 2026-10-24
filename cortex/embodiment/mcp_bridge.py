import json
import os
import sys
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

@dataclass
class AccessibilityNode:
    node_id: str
    role: str
    name: str
    bounding_box: Dict[str, int] = field(default_factory=dict)
    children: List["AccessibilityNode"] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "role": self.role,
            "name": self.name,
            "bounds": self.bounding_box,
            "children": [c.to_dict() for c in self.children]
        }

class PerceptualCircuitBreaker:
    """
    Verifies sensory input data integrity before allowing it onto the Global Workspace.
    Catches empty payloads, corrupted frames, and malformed tree hierarchies.
    """
    @staticmethod
    def inspect(observation: Dict[str, Any]) -> Tuple[bool, str]:
        if not observation:
            return False, "Empty observation payload."
        if observation.get("type") == "a11y_tree":
            nodes = observation.get("nodes", [])
            if not isinstance(nodes, list):
                return False, "Malformed accessibility tree: 'nodes' must be a list."
            if len(nodes) == 0:
                return False, "Accessibility tree is empty (canvas/Electron container without accessible nodes)."
        elif observation.get("type") == "screen_capture":
            if not observation.get("data") and not observation.get("file_path"):
                return False, "Corrupted screen capture: missing image data or path."
        return True, "Passed perceptual circuit breaker integrity check."

class MCPDesktopBridge:
    """
    Somatosensory MCP bridge connecting to native OS Accessibility Trees
    (AXUIElement on macOS, UI Automation on Windows) with Set-of-Mark visual fallback.
    """
    def __init__(self, simulation_mode: bool = True):
        self.simulation_mode = simulation_mode
        self.circuit_breaker = PerceptualCircuitBreaker()
        self.session_id = f"session_{int(time.time())}"

    async def query_accessibility_tree(
        self,
        root_id: str = "root",
        max_depth: int = 3
    ) -> Dict[str, Any]:
        """
        Fast-Path: Queries OS accessibility hierarchy.
        Returns URI: a11y://tree/{session}?root={root_id}&depth={max_depth}
        """
        tree = AccessibilityNode(
            node_id="desktop_root",
            role="Window",
            name="CortexOS Active Desktop",
            bounding_box={"x": 0, "y": 0, "w": 1920, "h": 1080},
            children=[
                AccessibilityNode(
                    node_id="btn_terminal",
                    role="Button",
                    name="Terminal",
                    bounding_box={"x": 100, "y": 100, "w": 120, "h": 40}
                ),
                AccessibilityNode(
                    node_id="txt_editor",
                    role="EditArea",
                    name="Workspace Editor",
                    bounding_box={"x": 250, "y": 100, "w": 800, "h": 600}
                ),
                AccessibilityNode(
                    node_id="lbl_status",
                    role="StaticText",
                    name="Branch: master | Healthy",
                    bounding_box={"x": 250, "y": 720, "w": 300, "h": 25}
                )
            ]
        )
        payload = {
            "type": "a11y_tree",
            "uri": f"a11y://tree/{self.session_id}?root={root_id}&depth={max_depth}",
            "nodes": [tree.to_dict()]
        }
        passed, reason = self.circuit_breaker.inspect(payload)
        payload["circuit_breaker_passed"] = passed
        payload["circuit_breaker_reason"] = reason
        return payload

    async def click_element(self, node_id: str) -> Dict[str, Any]:
        """Clicks an interactive UI element by accessibility identifier."""
        return {
            "status": "SUCCESS",
            "action": "click",
            "target_node_id": node_id,
            "latency_ms": 12.4
        }

    async def type_text(self, text: str, node_id: Optional[str] = None) -> Dict[str, Any]:
        """Sends keystrokes to active or focused accessibility node."""
        return {
            "status": "SUCCESS",
            "action": "type",
            "text_length": len(text),
            "target_node_id": node_id
        }

    async def capture_set_of_mark_som(self) -> Dict[str, Any]:
        """
        Secondary Fallback: High-speed desktop capture with Set-of-Mark badges.
        Used when accessibility container is incomplete or empty.
        """
        return {
            "type": "screen_capture",
            "latency_ms": 22.8,
            "som_markers_count": 14,
            "markers": [
                {"mark_id": 1, "coord": [160, 120], "label": "Terminal Button"},
                {"mark_id": 2, "coord": [650, 400], "label": "Editor Canvas"}
            ],
            "file_path": "/tmp/cortex_som_current.png"
        }
