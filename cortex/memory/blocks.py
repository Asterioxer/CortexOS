import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from jinja2 import Template

@dataclass
class MemoryBlock:
    label: str
    description: str
    value: str
    char_limit: int = 3000

    def append(self, content: str) -> str:
        new_val = f"{self.value}\n{content}".strip()
        if len(new_val) > self.char_limit:
            raise ValueError(
                f"Block '{self.label}' exceeded limit ({len(new_val)}/{self.char_limit} chars). "
                f"Call memory_rethink to distill before appending."
            )
        self.value = new_val
        return f"Successfully appended to block '{self.label}'."

    def replace(self, old_str: str, new_str: str) -> str:
        if old_str not in self.value:
            raise ValueError(f"Target string not found in block '{self.label}'.")
        updated = self.value.replace(old_str, new_str, 1)
        if len(updated) > self.char_limit:
            raise ValueError(f"Replacement exceeds char limit ({self.char_limit}) in '{self.label}'.")
        self.value = updated
        return f"Patched block '{self.label}'."

    def apply_patch(self, patch: str) -> str:
        """Appends or updates according to simple patch directive."""
        return self.append(patch)

    def rethink(self, new_condensed_value: str) -> str:
        """Condenses or rewrites block state during self-reflection."""
        if len(new_condensed_value) > self.char_limit:
            raise ValueError(f"Condensed value exceeds char limit ({self.char_limit}).")
        self.value = new_condensed_value.strip()
        return f"Block '{self.label}' updated via memory_rethink."

class WorkingMemoryManager:
    """
    Letta / CoALA Working Memory: 4 character-bounded self-editing in-context blocks
    compiled into prompt context via Jinja templates.
    """
    PROMPT_TEMPLATE = """
<memory_block label="persona_self" desc="{{ blocks.persona_self.description }}">
{{ blocks.persona_self.value }}
</memory_block>

<memory_block label="human_profile" desc="{{ blocks.human_profile.description }}">
{{ blocks.human_profile.value }}
</memory_block>

<memory_block label="workspace_state" desc="{{ blocks.workspace_state.description }}">
{{ blocks.workspace_state.value }}
</memory_block>

<memory_block label="scratchpad_stm" desc="{{ blocks.scratchpad_stm.description }}">
{{ blocks.scratchpad_stm.value }}
</memory_block>
""".strip()

    def __init__(self, p_self_text: Optional[str] = None, storage_path: str = ".cortex/working_memory_state.json"):
        self.storage_path = Path(storage_path)
        default_self = (
            "I am CortexOS, an autonomous, self-learning cognitive operating system "
            "embodied on this laptop. I think in the first person ('I'). I prioritize "
            "deterministic reversibility, epistemic provenance, and calibrated restraint. "
            "When I lack a capability, I synthesize and verify new modular tools."
        )
        self.blocks: Dict[str, MemoryBlock] = {
            "persona_self": MemoryBlock(
                label="persona_self",
                description="Core identity, ethical invariants, and ultimate objectives.",
                value=p_self_text or default_self,
                char_limit=3000
            ),
            "human_profile": MemoryBlock(
                label="human_profile",
                description="User preferences, coding styles, and active project guidelines.",
                value="User prefers concise answers, local-first execution, and verified undoable steps.",
                char_limit=3000
            ),
            "workspace_state": MemoryBlock(
                label="workspace_state",
                description="Current repository posture, active branches, and sleep-time learned context.",
                value="Workspace initialized at active project root. No pending merge conflicts.",
                char_limit=3000
            ),
            "scratchpad_stm": MemoryBlock(
                label="scratchpad_stm",
                description="Immediate focus, transient deductions, and active subgoals.",
                value="Awaiting perceptual triggers or user tasks.",
                char_limit=3000
            )
        }
        self.jinja_template = Template(self.PROMPT_TEMPLATE)
        self.load()

    def save(self):
        """Persists memory blocks to disk."""
        try:
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            data = {k: {"label": b.label, "description": b.description, "value": b.value, "char_limit": b.char_limit} for k, b in self.blocks.items()}
            self.storage_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except Exception:
            pass

    def load(self):
        """Loads memory blocks from disk if present."""
        if self.storage_path.exists():
            try:
                data = json.loads(self.storage_path.read_text(encoding="utf-8"))
                for k, v in data.items():
                    if k in self.blocks:
                        self.blocks[k].value = v.get("value", self.blocks[k].value)
            except Exception:
                pass

    def get_block(self, label: str) -> MemoryBlock:
        if label not in self.blocks:
            raise KeyError(f"Memory block '{label}' does not exist.")
        return self.blocks[label]

    def core_memory_append(self, block_label: str, content: str) -> str:
        res = self.get_block(block_label).append(content)
        self.save()
        return res

    def core_memory_replace(self, block_label: str, old_str: str, new_str: str) -> str:
        res = self.get_block(block_label).replace(old_str, new_str)
        self.save()
        return res

    def memory_rethink(self, block_label: str, new_value: str) -> str:
        res = self.get_block(block_label).rethink(new_value)
        self.save()
        return res

    def compile(self) -> str:
        """Renders the four in-context memory blocks into markdown system instructions."""
        return self.jinja_template.render(blocks=self.blocks)
