import os
import pytest
from pathlib import Path
from cortex.skills.crystallizer import AutopoieticSkillCrystallizer, AutomaticCurriculumGenerator
from cortex.memory.substrate import MemorySubstrate
from cortex.governance.sandbox import SandboxRunner
from cortex.inference.client import LocalInferenceClient

@pytest.mark.asyncio
async def test_autopoietic_skill_crystallization(tmp_path):
    skill_dir = tmp_path / "skills_lib"
    db_file = str(tmp_path / "skill_test.sqlite")
    
    memory = MemorySubstrate(db_file)
    sandbox = SandboxRunner(str(Path(os.getcwd()).resolve()))
    llm = LocalInferenceClient()
    
    crystallizer = AutopoieticSkillCrystallizer(
        llm_client=llm,
        memory_substrate=memory,
        sandbox_runner=sandbox,
        skill_dir=str(skill_dir)
    )
    
    # Run a task requiring tool synthesis
    subtask = {
        "action": "calculate_hash_manifest",
        "description": "Generate SHA256 integrity hash for core files.",
        "task_id": "test-crystallize-001"
    }
    
    result = await crystallizer.execute_or_synthesize(subtask)
    assert result["status"] == "SUCCESS"
    assert result["crystallized"] is True
    assert result["reusability_score"] > 8
    
    # Check that crystallized tool file exists on disk
    crystallized_files = list(skill_dir.glob("tool_*.py"))
    assert len(crystallized_files) >= 1
    
    # Verify skill was indexed in procedural memory database
    skills = await memory.search_skills("integrity hash")
    assert len(skills) >= 1
    assert "integrity hash" in skills[0]["docstring"].lower()

def test_automatic_curriculum_generator():
    gen = AutomaticCurriculumGenerator()
    b_task = gen.get_next_challenge("beginner")
    assert "level" in b_task
    assert b_task["level"] == "beginner"
    
    adv_task = gen.get_next_challenge("advanced")
    assert adv_task["level"] == "advanced"
