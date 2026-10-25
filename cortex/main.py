import argparse
import asyncio
import os
import sys
from pathlib import Path

# Ensure root repository is on sys.path for direct script execution
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import yaml
from cortex.inference.client import LocalInferenceClient
from cortex.memory.blocks import WorkingMemoryManager
from cortex.memory.substrate import MemorySubstrate
from cortex.governance.policy_engine import PolicyEngine
from cortex.governance.sandbox import SandboxRunner
from cortex.governance.checkpoint import GitShadowCheckpointManager
from cortex.skills.crystallizer import AutopoieticSkillCrystallizer
from cortex.workspace.tick_engine import GWACognitiveTickEngine
from cortex.daemon.event_bus import PerceptualDaemonBus
from cortex.sleep.consolidation import DigitalSleepPipeline

def load_core_self():
    p = Path("config/core_self.yaml")
    if p.exists():
        with open(p, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            return " ".join(data.get("p_self", {}).get("directives", []))
    return None

def build_cortex_stack():
    p_self_text = load_core_self()
    wm = WorkingMemoryManager(p_self_text=p_self_text)
    memory = MemorySubstrate("cortex_memory.sqlite")
    policy = PolicyEngine("config/policies.cedar")
    sandbox = SandboxRunner()
    llm = LocalInferenceClient(model="qwen2.5:3b")
    skills = AutopoieticSkillCrystallizer(
        llm_client=llm,
        memory_substrate=memory,
        sandbox_runner=sandbox
    )
    engine = GWACognitiveTickEngine(
        llm_client=llm,
        memory_substrate=memory,
        working_memory=wm,
        skill_engine=skills,
        policy_gate=policy
    )
    bus = PerceptualDaemonBus()
    sleep = DigitalSleepPipeline(
        memory_substrate=memory,
        working_memory=wm
    )
    return {
        "wm": wm,
        "memory": memory,
        "policy": policy,
        "sandbox": sandbox,
        "llm": llm,
        "skills": skills,
        "engine": engine,
        "bus": bus,
        "sleep": sleep
    }

async def cmd_tick(args):
    stack = build_cortex_stack()
    engine = stack["engine"]
    print(f"[CortexOS] Initializing Cognitive Tick (Input: '{args.input or 'Heartbeat'}')...")
    tag = await engine.run_cognitive_tick(external_input=args.input)
    print(f"[CortexOS] Tick #{engine.state.tick_id} Complete. Transition: {tag}")
    print(f"[CortexOS] Active Temperature: {engine.state.current_temperature:.2f}")
    if tag.user_response:
        print(f"\n[CortexOS Articulation]:\n{tag.user_response}\n")
    print(f"[CortexOS] Recent STM Trace:")
    for trace in engine.state.stm_buffer[-3:]:
        print(f"  > {trace}")

async def cmd_sleep(args):
    stack = build_cortex_stack()
    sleep_pipe = stack["sleep"]
    print("[CortexOS] Commencing Asynchronous Digital Sleep Consolidation...")
    report = await sleep_pipe.run_consolidation_cycle()
    print(f"[CortexOS] Digital Sleep Complete in {report.duration_seconds}s:")
    print(f"  - Atomic Engrams Extracted: {report.engrams_extracted}")
    print(f"  - Bi-Temporal Graph Edges Updated: {report.graph_edges_updated}")
    print(f"  - Codebase Files Pre-computed: {report.codebase_files_analyzed}")
    print(f"  - Composite Skills Crystallized: {report.composite_tools_crystallized}")
    print(f"  - LoRA Training Samples Prepared: {report.lora_training_samples_prepared}")

async def cmd_status(args):
    stack = build_cortex_stack()
    wm = stack["wm"]
    print("=" * 60)
    print(" CortexOS: Cognitive Operating System Status ")
    print("=" * 60)
    print("\n--- IN-CONTEXT WORKING MEMORY BLOCKS ---")
    for label, block in wm.blocks.items():
        print(f"[{label.upper()}] ({len(block.value)}/{block.char_limit} chars)")
        print(f"  {block.value[:140]}...")
    print("\n--- GOVERNANCE POSTURE ---")
    print(f"  Active Policy Gate: {stack['policy'].cedar_path}")
    print(f"  Shadow Checkpoint Directory: {stack['sandbox'].checkpoint_mgr.snapshots_dir}")
    print("=" * 60)

async def cmd_interact(args):
    from cortex.interactive import CortexInteractiveSession
    stack = build_cortex_stack()
    session = CortexInteractiveSession(stack)
    await session.run()

def cmd_web(args):
    from cortex.server import start_server
    print(f"[CortexOS] Starting Real-Time Neural Dashboard on http://{args.host}:{args.port}...")
    start_server(host=args.host, port=args.port)

def main():
    parser = argparse.ArgumentParser(description="CortexOS: Local-First Cognitive Operating System")
    subparsers = parser.add_subparsers(dest="command")

    tick_parser = subparsers.add_parser("tick", help="Execute a Global Workspace Cognitive Tick")
    tick_parser.add_argument("--input", "-i", type=str, default=None, help="Sensory / external perception string")

    sleep_parser = subparsers.add_parser("sleep", help="Run offline Digital Sleep consolidation")
    status_parser = subparsers.add_parser("status", help="Show system status and active memory blocks")

    interact_parser = subparsers.add_parser("interact", help="Launch real-time interactive terminal shell")
    
    web_parser = subparsers.add_parser("web", help="Launch real-time web UI dashboard")
    web_parser.add_argument("--host", default="127.0.0.1", help="Host interface (default: 127.0.0.1)")
    web_parser.add_argument("--port", type=int, default=8000, help="Port (default: 8000)")

    ui_parser = subparsers.add_parser("ui", help="Alias for web dashboard")
    ui_parser.add_argument("--host", default="127.0.0.1", help="Host interface (default: 127.0.0.1)")
    ui_parser.add_argument("--port", type=int, default=8000, help="Port (default: 8000)")

    args = parser.parse_args()
    if args.command == "tick":
        asyncio.run(cmd_tick(args))
    elif args.command == "sleep":
        asyncio.run(cmd_sleep(args))
    elif args.command == "status":
        asyncio.run(cmd_status(args))
    elif args.command == "interact":
        asyncio.run(cmd_interact(args))
    elif args.command in ["web", "ui"]:
        cmd_web(args)
    else:
        # Default to interactive if no command specified
        asyncio.run(cmd_interact(args))

if __name__ == "__main__":
    main()
