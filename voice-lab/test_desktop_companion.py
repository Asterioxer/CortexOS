"""
Test suite to verify DesktopCompanionHUD syntax, window layout, canvas rendering, and event dispatch.
"""
import sys
import time
from desktop_companion import DesktopCompanionHUD

def test_hud():
    print("[*] Initializing DesktopCompanionHUD (headless simulation)...")
    # Initialize without booting heavy LLM models for this unit test
    hud = DesktopCompanionHUD(start_assistant_core=False)
    
    # Test canvas rendering
    print("[*] Testing canvas render frame...")
    hud._render_canvas_frame()
    
    # Test event dispatch
    print("[*] Testing event queue dispatch...")
    hud.event_queue.put(("state", "listening"))
    hud.event_queue.put(("heard", "Test spoken voice input"))
    hud.event_queue.put(("response", "Test assistant reply"))
    hud.event_queue.put(("persona", "jenny"))
    hud._poll_event_queue()
    
    assert hud.current_state == "listening", f"State mismatch: {hud.current_state}"
    assert hud.active_persona == "jenny", f"Persona mismatch: {hud.active_persona}"
    assert hud.user_text_lbl.cget("text") == "\"Test spoken voice input\""
    assert hud.asst_text_lbl.cget("text") == "Test assistant reply"
    
    # Test unlock event
    print("[*] Testing unlock event simulation...")
    hud.event_queue.put(("unlock", "Good morning Soham! All systems online."))
    hud._poll_event_queue()
    assert "Good morning Soham" in hud.asst_text_lbl.cget("text")
    
    # Clean up
    hud.root.destroy()
    print("[+] All DesktopCompanionHUD tests passed successfully!")

if __name__ == "__main__":
    test_hud()
