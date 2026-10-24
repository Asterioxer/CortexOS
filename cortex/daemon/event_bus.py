import asyncio
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Coroutine, Dict, List, Optional
from cortex.embodiment.mcp_bridge import PerceptualCircuitBreaker

class TriggerType(str, Enum):
    CLOCK = "CLOCK"
    CHANGE = "CHANGE"
    MESSAGE = "MESSAGE"

@dataclass
class CognitiveEvent:
    trigger_type: TriggerType
    source: str
    payload: Dict[str, Any]
    timestamp: float = field(default_factory=time.time)

class PerceptualDaemonBus:
    """
    Layer 1 Event-Driven Perceptual Daemon.
    Listens for Clock (Time), Change (OS/Filesystem/Terminal), and Message (Inbox) triggers.
    Enforces Perceptual Circuit Breaker before pushing events to Layer 2 Global Workspace.
    """
    def __init__(self):
        self.event_queue: asyncio.Queue[CognitiveEvent] = asyncio.Queue()
        self.circuit_breaker = PerceptualCircuitBreaker()
        self.running = False
        self._handlers: List[Callable[[CognitiveEvent], Coroutine[Any, Any, None]]] = []
        self.ambient_context_buffer: List[Dict[str, Any]] = []

    def register_handler(self, handler: Callable[[CognitiveEvent], Coroutine[Any, Any, None]]):
        self._handlers.append(handler)

    async def emit_clock_trigger(self, schedule_name: str, payload: Optional[Dict] = None):
        """Fires scheduled heartbeat or time trigger."""
        event = CognitiveEvent(
            trigger_type=TriggerType.CLOCK,
            source=schedule_name,
            payload=payload or {"status": "heartbeat_tick"}
        )
        await self.event_queue.put(event)

    async def emit_change_trigger(self, source_subsystem: str, change_detail: Dict[str, Any]):
        """Fires push-based change trigger (e.g. filesystem edit, window focus change)."""
        event = CognitiveEvent(
            trigger_type=TriggerType.CHANGE,
            source=source_subsystem,
            payload=change_detail
        )
        await self.event_queue.put(event)

    async def emit_message_trigger(self, sender: str, message_text: str):
        """Fires asynchronous inbox message trigger from user or peer agent."""
        event = CognitiveEvent(
            trigger_type=TriggerType.MESSAGE,
            source=sender,
            payload={"message": message_text}
        )
        await self.event_queue.put(event)

    async def run_step(self, timeout: float = 1.0) -> Optional[CognitiveEvent]:
        """Processes one pending event from queue with perceptual circuit breaker validation."""
        try:
            event = await asyncio.wait_for(self.event_queue.get(), timeout=timeout)
            
            # Inspect sensory data integrity
            passed, reason = self.circuit_breaker.inspect(event.payload)
            if not passed:
                return None

            # Maintain ambient context buffer (most recent 10 items)
            self.ambient_context_buffer.append({
                "type": event.trigger_type.value,
                "source": event.source,
                "time": event.timestamp,
                "summary": str(event.payload)[:100]
            })
            if len(self.ambient_context_buffer) > 10:
                self.ambient_context_buffer.pop(0)

            # Broadcast to registered cognitive tick handlers
            for handler in self._handlers:
                await handler(event)

            self.event_queue.task_done()
            return event
        except asyncio.TimeoutError:
            return None
