import time
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

@dataclass
class StallBreaker:
    """
    Monitors perceptual visual/tree deltas and listens for hardware panic stop switches.
    """
    stall_threshold_consecutive: int = 3
    consecutive_zero_deltas: int = 0
    panic_active: bool = False
    panic_reason: Optional[str] = None
    last_action_timestamp: float = field(default_factory=time.time)

    def trigger_panic(self, reason: str = "Hardware killswitch triggered"):
        self.panic_active = True
        self.panic_reason = reason

    def reset_panic(self):
        self.panic_active = False
        self.panic_reason = None

    def is_panic_triggered(self) -> bool:
        return self.panic_active

    def record_delta(self, visual_diff_score: float, tree_node_count_diff: int) -> bool:
        """
        Records sensory delta following an action.
        Returns True if execution has stalled and must be halted.
        """
        if visual_diff_score < 0.001 and tree_node_count_diff == 0:
            self.consecutive_zero_deltas += 1
        else:
            self.consecutive_zero_deltas = 0

        self.last_action_timestamp = time.time()
        return self.is_stalled()

    def is_stalled(self) -> bool:
        return self.consecutive_zero_deltas >= self.stall_threshold_consecutive

    def check_mouse_panic_coordinate(self, x: int, y: int) -> bool:
        """Moving cursor to (0,0) triggers immediate hardware panic stop."""
        if x == 0 and y == 0:
            self.trigger_panic("Mouse moved to screen coordinate (0, 0)")
            return True
        return False

    def check_keyboard_panic(self, ctrl: bool, alt: bool, shift: bool, key: str) -> bool:
        """Pressing Ctrl+Alt+Shift+Q triggers immediate hardware panic stop."""
        if ctrl and alt and shift and key.upper() == "Q":
            self.trigger_panic("Panic hotkey Ctrl+Alt+Shift+Q pressed")
            return True
        return False
