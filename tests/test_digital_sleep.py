import pytest
from cortex.sleep.consolidation import DigitalSleepPipeline
from cortex.memory.substrate import MemorySubstrate
from cortex.memory.blocks import WorkingMemoryManager

@pytest.mark.asyncio
async def test_digital_sleep_pipeline(tmp_path):
    db_file = str(tmp_path / "sleep_test.sqlite")
    memory = MemorySubstrate(db_file)
    wm = WorkingMemoryManager()
    
    # Pre-populate raw episodes in Tier 1 SQLite
    for i in range(3):
        memory.record_raw_episode(
            event_type="cognitive_tick",
            tick_id=i+1,
            input_payload=f"Perceptual event {i}",
            thought_trace=f"[Tick {i+1}] I observed the git status and memory state.",
            action_taken="read_status",
            outcome="SUCCESS"
        )
        
    pipeline = DigitalSleepPipeline(
        memory_substrate=memory,
        working_memory=wm,
        workspace_dir=str(tmp_path)
    )
    
    report = await pipeline.run_consolidation_cycle()
    
    # Stage 1 verification: Engrams extracted and graph edges updated
    assert report.engrams_extracted >= 3
    assert report.graph_edges_updated >= 3
    
    # Stage 2 verification: Workspace state updated with learned context
    ws_val = wm.get_block("workspace_state").value
    assert "Sleep-Time Pre-computation" in ws_val
    
    # Stage 3 & 4 verification: Macro consolidation and LoRA dataset generated
    assert report.composite_tools_crystallized >= 1
    assert report.lora_training_samples_prepared >= 1
