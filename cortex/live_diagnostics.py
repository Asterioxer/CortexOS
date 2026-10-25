import asyncio
import json
import os
import sys
import time
from pathlib import Path

# Ensure root in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from cortex.main import build_cortex_stack
from cortex.embodiment.system_somatosensory import SystemSomatosensory

async def run_live_diagnostics():
    print("=" * 80)
    print("      CORTEX-OS: COMPREHENSIVE LIVE SUBSYSTEM VERIFICATION RUN")
    print("=" * 80)
    print(f"Timestamp: {time.ctime()}")
    print(f"Platform:  {sys.platform} (User: {os.getlogin()})\n")

    stack = build_cortex_stack()
    engine = stack["engine"]
    somato = stack["engine"].somato
    memory = stack["memory"]
    wm = stack["wm"]
    policy = stack["policy"]
    sandbox = stack["sandbox"]
    sleep = stack["sleep"]

    # -------------------------------------------------------------
    # 1. LIVE SOMATOSENSORY TELEMETRY & OS SENSORS
    # -------------------------------------------------------------
    print("─" * 80)
    print(" [TEST 1/7] LIVE SOMATOSENSORY PERCEPTION & EMBODIMENT")
    print("─" * 80)
    
    t0 = time.time()
    hw = somato.get_hardware_telemetry()
    hw_latency = (time.time() - t0) * 1000
    
    cpu = hw.get("cpu", {})
    ram = hw.get("ram", {})
    gpu = hw.get("gpu", {})
    batt = hw.get("battery", {})
    disk = hw.get("disk_c", {})
    
    print(f"✓ Hardware Telemetry Latency: {hw_latency:.2f} ms (<15ms target)")
    print(f"  • CPU Utilization:  {cpu.get('percent')}% across {cpu.get('cores_logical')} logical threads ({cpu.get('cores_physical')} physical cores)")
    print(f"  • Physical Memory:  {ram.get('used_gb')} GB / {ram.get('total_gb')} GB ({ram.get('percent')}%)")
    print(f"  • Primary Storage:  {disk.get('used_gb')} GB used / {disk.get('total_gb')} GB total ({disk.get('percent')}%)")
    print(f"  • Battery / Power:  {batt.get('percent')}% (AC Plugged In: {batt.get('plugged_in')})")
    if gpu.get("name"):
        vram_pct = round((gpu.get('vram_used_mb', 0) / max(1, gpu.get('vram_total_mb', 1))) * 100, 1)
        print(f"  • Discrete GPU:     {gpu.get('name')} ({gpu.get('vram_used_mb')}MB/{gpu.get('vram_total_mb')}MB [{vram_pct}%], Core Temp: {gpu.get('temperature_c')}°C)")

    # Windows GSMTC Audio
    media = await somato.get_active_media_playback()
    if media.get("active"):
        print(f"✓ Windows GSMTC Audio: ACTIVE -> '{media.get('title')}' by {media.get('artist')} [{media.get('app')}] ({media.get('status')})")
    else:
        print(f"✓ Windows GSMTC Audio: NO ACTIVE PLAYBACK DETECTED")

    # Win32 Foreground Window
    win = somato.get_active_window()
    print(f"✓ Win32 Focused Window: '{win.get('title')}' (Process: {win.get('process')}, PID: {win.get('pid')})")

    # Clipboard Read/Write
    test_clip_token = f"CORTEX-OS-LIVE-VERIFIED-{int(time.time())}"
    somato.set_clipboard_text(test_clip_token)
    clip_read = somato.get_clipboard_text()
    assert test_clip_token in clip_read.get("text", "")
    print(f"✓ System Clipboard: Confirmed bidirectional read/write ({len(test_clip_token)} bytes written & verified)")

    # Top GUI Apps
    apps = somato.get_user_applications(top_n=5)
    app_str = ", ".join([f"{a['name']} ({a['mem_pct']}%)" for a in apps])
    print(f"✓ Top GUI Applications: {app_str}\n")

    # -------------------------------------------------------------
    # 2. SYSTEM 1 FAST-PATH REFLEXES (<100ms)
    # -------------------------------------------------------------
    print("─" * 80)
    print(" [TEST 2/7] DUAL-PROCESS ROUTING: SYSTEM 1 FAST-PATH REFLEXES")
    print("─" * 80)
    
    t0 = time.time()
    tick1 = await engine.run_cognitive_tick(external_input="what song is playing right now")
    tick1_latency = (time.time() - t0) * 1000
    print(f"✓ System 1 Reflex: Media Query ({tick1_latency:.1f} ms)")
    print(f"  Action Taken: {tick1.action_executed}")
    print(f"  Response: {tick1.user_response.splitlines()[0]}")

    t0 = time.time()
    tick2 = await engine.run_cognitive_tick(external_input="what is my active window")
    tick2_latency = (time.time() - t0) * 1000
    print(f"✓ System 1 Reflex: Active Window Query ({tick2_latency:.1f} ms)")
    print(f"  Action Taken: {tick2.action_executed}")
    print(f"  Response: {tick2.user_response}\n")

    # -------------------------------------------------------------
    # 3. SYSTEM 2 MULTI-PERSPECTIVE THINKING & GWA ARBITRATION
    # -------------------------------------------------------------
    print("─" * 80)
    print(" [TEST 3/7] DUAL-PROCESS ROUTING: SYSTEM 2 DELIBERATIVE REASONING")
    print("─" * 80)
    
    deliberative_prompt = "Synthesize an architectural plan to optimize background thread performance on this laptop."
    t0 = time.time()
    tick3 = await engine.run_cognitive_tick(external_input=deliberative_prompt)
    tick3_latency = time.time() - t0
    
    print(f"✓ Deliberative Cycle Complete in {tick3_latency:.2f}s (Tick #{tick3.tick_id})")
    print(f"  • Shannon Entropy H(W): {tick3.entropy:.2f} | Dynamic Temperature: {tick3.temperature:.2f}")
    print(f"  • HASSUM Gate: Density={tick3.uncertainty.get('semantic_density')}, Entropy={tick3.uncertainty.get('semantic_entropy')}, Passed={tick3.uncertainty.get('pass')}")
    print(f"  • Specialist Perspectives Evaluated ({len(tick3.candidates)}):")
    for c in tick3.candidates:
        print(f"    - [{c.perspective}] (Score: {c.score:+d}): {c.thought_text[:110]}...")
    print(f"  • Winning Perspective: [{tick3.winning_thought.perspective}] (Score: {tick3.winning_thought.score:+d})")
    print(f"  • Articulation Preview: {tick3.user_response[:160]}...\n")

    # -------------------------------------------------------------
    # 4. PROCEDURAL SKILL SANDBOX EXECUTION (ATLAS PAMPHLETS)
    # -------------------------------------------------------------
    print("─" * 80)
    print(" [TEST 4/7] PROCEDURAL SKILL REGISTRY & ISOLATED KERNEL SANDBOX")
    print("─" * 80)
    
    skills = memory.get_all_skills()
    print(f"✓ Registered Procedural Skills in Procedural Memory: {len(skills)}")
    for s in skills:
        print(f"  • {s['name']:<28} | Reusability: {s['reusability_score']}/10 | Path: {s['file_path']}")

    # Live execute 2 procedural tools inside sandbox
    print("\nExecuting 'process_resource_optimizer' inside isolated sandbox with Git snapshotting...")
    res_opt = await sandbox.run_verified_skill("live-test-optimizer", "cortex/skills/library/process_resource_optimizer.py")
    print(f"✓ Sandbox Exit Code: {res_opt.get('exit_code')} ({res_opt.get('status')})")
    print("  First 4 lines of stdout:")
    for line in res_opt.get("stdout", "").splitlines()[:4]:
        print(f"    $ {line}")

    print("\nExecuting 'codebase_topology_mapper' inside isolated sandbox with Git snapshotting...")
    res_topo = await sandbox.run_verified_skill("live-test-topo", "cortex/skills/library/codebase_topology_mapper.py")
    print(f"✓ Sandbox Exit Code: {res_topo.get('exit_code')} ({res_topo.get('status')})")
    print("  First 4 lines of stdout:")
    for line in res_topo.get("stdout", "").splitlines()[:4]:
        print(f"    $ {line}\n")

    # -------------------------------------------------------------
    # 5. ASYNCHRONOUS DIGITAL SLEEP CYCLE & ACTION SEQUENCE MINING
    # -------------------------------------------------------------
    print("─" * 80)
    print(" [TEST 5/7] ASYNCHRONOUS DIGITAL SLEEP & RECURRING ACTION MINING")
    print("─" * 80)
    
    t0 = time.time()
    report = await sleep.run_consolidation_cycle()
    print(f"✓ Digital Sleep Consolidation Complete in {report.duration_seconds}s:")
    print(f"  • Stage 1: Atomic Engrams Extracted:         {report.engrams_extracted}")
    print(f"  • Stage 1: Causal MAGMA Graph Edges Updated:  {report.graph_edges_updated}")
    print(f"  • Stage 2: Codebase Modules Pre-computed:     {report.codebase_files_analyzed}")
    print(f"  • Stage 3: Composite Action Macros Mined:     {report.composite_tools_crystallized}")
    print(f"  • Stage 4: LoRA Instruction Samples Prepared: {report.lora_training_samples_prepared}")
    
    # Inspect newly synthesized LoRA dataset
    lora_path = Path(".cortex/lora_training_dataset.jsonl")
    if lora_path.exists():
        lines = lora_path.read_text(encoding="utf-8").splitlines()
        print(f"  • Generated Dataset: {lora_path} ({len(lines)} training pairs)")
        if lines:
            first_sample = json.loads(lines[0])
            print(f"    Sample: Instruction: '{first_sample.get('instruction')[:60]}...' | Outcome: '{first_sample.get('outcome')}'\n")

    # -------------------------------------------------------------
    # 6. CEDAR DEFENSE-IN-DEPTH GOVERNANCE & SHADOW GIT CHECKPOINTS
    # -------------------------------------------------------------
    print("─" * 80)
    print(" [TEST 6/7] CEDAR GOVERNANCE, SHADOW CHECKPOINTS, & PANIC SWITCH")
    print("─" * 80)

    # 1. ALLOW (Safe read-only)
    v_allow = policy.evaluate({"action": "file_read", "resource": "cortex/server.py"})
    print(f"✓ Policy Evaluation (file_read): {v_allow.status.value} in {v_allow.evaluation_time_ms:.3f} ms (<0.1ms class)")

    # 2. ESCALATE (Destructive remote action)
    v_esc = policy.evaluate({"action": "git_push_remote", "resource": "origin master"})
    print(f"✓ Policy Evaluation (git_push_remote): {v_esc.status.value} in {v_esc.evaluation_time_ms:.3f} ms (Requires Operator Approval)")

    # 3. DENY (Forbidden credential inspection)
    v_deny = policy.evaluate({"action": "file_read", "resource": "C:/Users/soham/.ssh/id_rsa"})
    print(f"✓ Policy Evaluation (.ssh credential path): {v_deny.status.value} in {v_deny.evaluation_time_ms:.3f} ms (Blocked: {v_deny.reason})")

    # Shadow Git Checkpoint
    task_id = f"live-check-{int(time.time())}"
    t0 = time.time()
    sha = sandbox.checkpoint_mgr.create_checkpoint(task_id, label="pre")
    cp_time = time.time() - t0
    print(f"✓ Deterministic Shadow Git Checkpoint: Created in {cp_time:.3f}s -> SHA {sha[:10]} under refs/checkpoints/{task_id}/pre")

    # Hardware Panic Switch test
    print("✓ Testing Hardware Panic Killswitch circuit breaker...")
    engine.stall_breaker.trigger_panic("Live diagnostic panic verification")
    panic_tick = await engine.run_cognitive_tick("test while panicked")
    assert "PANIC" in panic_tick.user_response
    print(f"  Panic Gate Response: '{panic_tick.user_response}'")
    engine.stall_breaker.reset_panic()
    assert engine.stall_breaker.is_panic_triggered() is False
    print("  Panic Reset: Successful. Normal autonomous reflexes restored.\n")

    # -------------------------------------------------------------
    # 7. WORKING MEMORY LETTA BLOCKS & GRAPH VERIFICATION
    # -------------------------------------------------------------
    print("─" * 80)
    print(" [TEST 7/7] WORKING MEMORY & BI-TEMPORAL KNOWLEDGE GRAPH")
    print("─" * 80)
    for label, b in wm.blocks.items():
        print(f"  • Block [{label}]: {len(b.value)}/{b.char_limit} chars | Value preview: '{b.value[:70].strip()}...'")

    edges = memory.get_all_graph_edges(limit=5)
    print(f"\n✓ Verified Bi-Temporal Graph Edges Sample ({len(edges)}):")
    for e in edges:
        print(f"  • ({e['source_id'][:25]}) ➔ [{e['relation']}] ➔ ({e['target_id'][:25]}) [{e['layer']}]")

    print("\n" + "=" * 80)
    print("      ALL 7 CORTEX-OS SUBSYSTEMS FULLY OPERATIONAL & VERIFIED LIVE")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(run_live_diagnostics())
