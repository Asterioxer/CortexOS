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

def main():
    parser = argparse.ArgumentParser(description="CortexOS: Local-First Cognitive Operating System")
    subparsers = parser.add_subparsers(dest="command")

    tick_parser = subparsers.add_parser("tick", help="Execute a Global Workspace Cognitive Tick")
    tick_parser.add_argument("--input", "-i", type=str, default=None, help="Sensory / external perception string")

    sleep_parser = subparsers.add_parser("sleep", help="Run offline Digital Sleep consolidation")
    status_parser = subparsers.add_parser("status", help="Show system status and active memory blocks")

    args = parser.parse_args()
    if args.command == "tick":
        asyncio.run(cmd_tick(args))
    elif args.command == "sleep":
        asyncio.run(cmd_sleep(args))
    elif args.command == "status":
        asyncio.run(cmd_status(args))
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
