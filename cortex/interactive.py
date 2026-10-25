import asyncio
import os
import sys
import time
from typing import Any, Dict, Optional

# ANSI color styling for immersive terminal experience
C_RESET = "\033[0m"
C_BOLD = "\033[1m"
C_DIM = "\033[2m"
C_BLUE = "\033[34m"
C_CYAN = "\033[36m"
C_GREEN = "\033[32m"
C_YELLOW = "\033[33m"
C_RED = "\033[31m"
C_MAGENTA = "\033[35m"

class CortexInteractiveSession:
    """
    Real-Time Interactive Terminal Shell for CortexOS.
    Maintains continuous cognitive monologue, ambient background ticks,
    live GWA deliberation streaming, and interactive human-in-the-loop hold cards.
    """
    def __init__(self, stack: Dict[str, Any]):
        self.stack = stack
        self.engine = stack["engine"]
        self.wm = stack["wm"]
        self.memory = stack["memory"]
        self.skills = stack["skills"]
        self.sleep = stack["sleep"]
        self.ambient_active = False
        self._running = True

    def print_banner(self):
        banner = f"""
{C_CYAN}{C_BOLD}========================================================================{C_RESET}
{C_CYAN}{C_BOLD}   CortexOS: Local-First Autonomous Cognitive Operating System          {C_RESET}
{C_CYAN}{C_BOLD}========================================================================{C_RESET}
{C_DIM}Embodied Dynamic Brain | GWA Cognitive Tick | Dual-Process Routing (S1/S2)
Letta 4-Tier Memory | Autopoietic Skill Crystallizer | Digital Sleep
Hardware Tier: RTX 3050 Laptop GPU (4GB VRAM) | 24GB Unified RAM | Ollama{C_RESET}

{C_YELLOW}Type your request, prompt, or task in natural language.{C_RESET}
{C_DIM}Commands: /status, /blocks, /graph, /skills, /sleep, /ambient on|off, /help, /exit{C_RESET}
{C_CYAN}------------------------------------------------------------------------{C_RESET}
"""
        print(banner)

    async def run(self):
        self.print_banner()
        ambient_task = asyncio.create_task(self._ambient_background_loop())
        
        loop = asyncio.get_running_loop()
        try:
            while self._running:
                # Prompt user for input asynchronously
                user_msg = await loop.run_in_executor(None, self._get_input)
                if not user_msg:
                    continue

                user_msg = user_msg.strip()
                if user_msg.startswith("/"):
                    await self._handle_command(user_msg)
                else:
                    await self._handle_user_prompt(user_msg)
        finally:
            self._running = False
            ambient_task.cancel()

    def _get_input(self) -> str:
        try:
            return input(f"{C_BOLD}{C_GREEN}cortex>{C_RESET} ")
        except (EOFError, KeyboardInterrupt):
            self._running = False
            return "/exit"

    async def _handle_command(self, cmd_str: str):
        parts = cmd_str.split(maxsplit=2)
        cmd = parts[0].lower()

        if cmd in ["/exit", "/quit"]:
            print(f"\n{C_CYAN}[CortexOS] Preserving working memory state. Entering sleep posture. Goodbye.{C_RESET}")
            self._running = False

        elif cmd == "/help":
            print(f"""
{C_BOLD}Available Commands:{C_RESET}
  {C_CYAN}/status{C_RESET}         - Inspect current cognitive posture and governance gates
  {C_CYAN}/blocks{C_RESET}         - View active Letta Working Memory Blocks
  {C_CYAN}/graph{C_RESET}          - Query recent bi-temporal knowledge graph edges and engrams
  {C_CYAN}/skills{C_RESET}         - List crystallized procedural tools and ATLAS pamphlets
  {C_CYAN}/sleep{C_RESET}          - Trigger offline 4-stage digital sleep consolidation
  {C_CYAN}/ambient [on|off]{C_RESET} - Toggle ambient background cognitive tick (default: off)
  {C_CYAN}/clear{C_RESET}          - Clear the terminal screen
  {C_CYAN}/exit{C_RESET}           - Exit CortexOS
""")

        elif cmd == "/status":
            print(f"\n{C_BOLD}--- CORTEXOS COGNITIVE STATE ---{C_RESET}")
            print(f"  Tick ID: {self.engine.state.tick_id}")
            print(f"  Base Temperature: {self.engine.state.base_temperature:.2f} | Active: {self.engine.state.current_temperature:.2f}")
            print(f"  Active Policy Gate: {self.stack['policy'].cedar_path}")
            print(f"  Ambient Mode: {'ACTIVE (15s)' if self.ambient_active else 'STANDBY'}")

        elif cmd == "/blocks":
            print(f"\n{C_BOLD}--- IN-CONTEXT WORKING MEMORY BLOCKS ---{C_RESET}")
            for label, block in self.wm.blocks.items():
                print(f"{C_MAGENTA}[{label.upper()}]{C_RESET} ({len(block.value)}/{block.char_limit} chars)")
                print(f"  {C_DIM}{block.value}{C_RESET}\n")

        elif cmd == "/graph":
            print(f"\n{C_BOLD}--- BI-TEMPORAL KNOWLEDGE GRAPH (MAGMA) ---{C_RESET}")
            facts = self.memory.query_graph_at_time(time.time(), limit=10)
            if not facts:
                print(f"  {C_DIM}No active graph edges found.{C_RESET}")
            for f in facts:
                print(f"  {C_CYAN}({f['source_id']}){C_RESET} --[{f['relation']}]--> {C_GREEN}({f['target_id']}){C_RESET} {C_DIM}(layer: {f['layer']}){C_RESET}")

        elif cmd == "/skills":
            print(f"\n{C_BOLD}--- AUTOPOIETIC PROCEDURAL SKILL LIBRARY ---{C_RESET}")
            skills = await self.memory.search_skills("", top_k=10)
            if not skills:
                print(f"  {C_DIM}No crystallized tools registered yet.{C_RESET}")
            for s in skills:
                print(f"  {C_GREEN}* {s['name']}{C_RESET} (Score: {s['score']}/10)")
                print(f"    {C_DIM}{s['docstring']}{C_RESET}")

        elif cmd == "/sleep":
            print(f"\n{C_YELLOW}[CortexOS] Initiating Digital Sleep consolidation cycle...{C_RESET}")
            report = await self.sleep.run_consolidation_cycle()
            print(f"{C_GREEN}[CortexOS] Sleep cycle complete in {report.duration_seconds}s:{C_RESET}")
            print(f"  - Extracted engrams: {report.engrams_extracted}")
            print(f"  - Updated graph edges: {report.graph_edges_updated}")
            print(f"  - Pre-computed files: {report.codebase_files_analyzed}")
            print(f"  - Composite tools: {report.composite_tools_crystallized}")
            print(f"  - LoRA samples prepared: {report.lora_training_samples_prepared}")

        elif cmd == "/ambient":
            if len(parts) > 1 and parts[1].lower() in ["on", "start", "enable"]:
                self.ambient_active = True
                print(f"{C_GREEN}[CortexOS] Ambient background cognitive tick activated (heartbeat: 15s).{C_RESET}")
            elif len(parts) > 1 and parts[1].lower() in ["off", "stop", "disable"]:
                self.ambient_active = False
                print(f"{C_YELLOW}[CortexOS] Ambient background cognitive tick deactivated.{C_RESET}")
            else:
                print(f"Usage: /ambient on | /ambient off (current: {'ON' if self.ambient_active else 'OFF'})")

        elif cmd == "/clear":
            os.system("cls" if os.name == "nt" else "clear")
            self.print_banner()

        else:
            print(f"{C_RED}Unknown command: {cmd}. Type /help for available options.{C_RESET}")

    async def _handle_user_prompt(self, prompt: str):
        print(f"\n{C_DIM}[Stage: Perceive]{C_RESET} Analyzing intent and formulating attention recall...")
        t0 = time.time()
        
        result = await self.engine.run_cognitive_tick(external_input=prompt)
        elapsed = time.time() - t0

        # Render Thought Monologue
        if result.candidates:
            print(f"{C_DIM}[Stage: Think]{C_RESET} Evaluated {len(result.candidates)} candidate perspectives:")
            for c in result.candidates:
                score_str = f"[{c.score:+d}]" if c.score else ""
                print(f"  {C_BLUE}* {c.perspective}:{C_RESET} {c.thought_text} {C_YELLOW}{score_str}{C_RESET}")

        print(
            f"{C_DIM}[Stage: Arbitrate]{C_RESET} Transition: {C_BOLD}{result.transition}{C_RESET} | "
            f"Entropy H(W): {result.entropy:.2f} | Temp: {result.temperature:.2f}"
        )

        # Check for Interactive Hold Card (ESCALATE)
        if result.hold_card:
            print(f"\n{C_RED}{C_BOLD}!!! GOVERNANCE CIRCUIT BREAKER (ESCALATE) !!!{C_RESET}")
            print(f"{C_YELLOW}Action requires explicit human approval:{C_RESET}")
            print(f"  Action: {result.hold_card.get('action')}")
            print(f"  Reason: {result.hold_card.get('reason')}")
            print(f"  Blast Radius: {result.hold_card.get('predicted_blast_radius')}")
            
            loop = asyncio.get_running_loop()
            choice = await loop.run_in_executor(None, lambda: input(f"{C_BOLD}Approve execution? (y/N): {C_RESET}").strip().lower())
            if choice in ["y", "yes"]:
                print(f"{C_GREEN}[CortexOS] Human approval granted. Resuming execution...{C_RESET}")
                resumed = await self.engine.run_cognitive_tick(
                    external_input=prompt, human_approval=True
                )
                print(f"\n{C_CYAN}{C_BOLD}CortexOS:{C_RESET} {resumed.user_response}\n")
                return
            else:
                print(f"{C_YELLOW}[CortexOS] Action rejected by operator. State rollback verified.{C_RESET}\n")
                return

        # Render First-Person Articulation
        if result.action_result and result.action_result.get("stdout"):
            print(f"{C_GREEN}[Output]:{C_RESET} {result.action_result.get('stdout').strip()}")

        print(f"\n{C_CYAN}{C_BOLD}CortexOS ({elapsed:.1f}s):{C_RESET} {result.user_response}\n")

    async def _ambient_background_loop(self):
        """Runs periodic ambient cognitive ticks when enabled."""
        while self._running:
            await asyncio.sleep(15)
            if self.ambient_active and self._running:
                result = await self.engine.run_cognitive_tick(external_input=None)
                if result.transition == "[RESPONSE]":
                    print(f"\n{C_DIM}[Ambient Notice Tick #{result.tick_id}]: {result.user_response}{C_RESET}\n{C_BOLD}{C_GREEN}cortex>{C_RESET} ", end="", flush=True)
