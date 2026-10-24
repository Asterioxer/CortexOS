import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional
from cortex.governance.sandbox import SandboxRunner
from cortex.memory.substrate import MemorySubstrate

class AutomaticCurriculumGenerator:
    """
    Proposes progressive self-directed tasks (from easy to challenging)
    around user-selected applications so CortexOS masters unfamiliar software.
    """
    CURRICULUM_TEMPLATES = [
        {"level": "beginner", "task": "Inspect active Git branch and verify working tree status."},
        {"level": "beginner", "task": "List all modified files in repository and calculate diff line count."},
        {"level": "intermediate", "task": "Scan project directories for dangling .pyc and temporary cache files."},
        {"level": "intermediate", "task": "Extract memory and CPU footprint telemetry and write regression report."},
        {"level": "advanced", "task": "Synthesize a multi-file dependency topology mapper and verify output format."}
    ]

    def get_next_challenge(self, current_level: str = "beginner") -> Dict[str, str]:
        matching = [c for c in self.CURRICULUM_TEMPLATES if c["level"] == current_level]
        return matching[0] if matching else self.CURRICULUM_TEMPLATES[0]

class AutopoieticSkillCrystallizer:
    """
    Implements FRIDAY/Voyager self-coding skill acquisition and ATLAS pamphlets.
    Synthesizes code, executes in isolated sandbox with Git checkpointing,
    critiques reusability (0-10), self-corrects up to 3 times, and crystallizes verified tools.
    """
    def __init__(
        self,
        llm_client,
        memory_substrate: MemorySubstrate,
        sandbox_runner: SandboxRunner,
        skill_dir: str = "cortex/skills/library"
    ):
        self.llm = llm_client
        self.vdb = memory_substrate
        self.sandbox = sandbox_runner
        self.skill_dir = Path(skill_dir).resolve()
        self.skill_dir.mkdir(parents=True, exist_ok=True)
        self.curriculum = AutomaticCurriculumGenerator()

    async def execute_or_synthesize(self, subtask: Dict[str, Any]) -> Dict[str, Any]:
        task_desc = subtask.get("description", str(subtask.get("action", "unspecified_task")))
        task_id = subtask.get("task_id", f"task_{abs(hash(task_desc)) % 100000}")

        # Step 1: Configurator dense retrieval over Procedural Memory
        matches = await self.vdb.search_skills(query=task_desc, top_k=3)
        if matches and matches[0].get("similarity", 0.0) >= 0.82:
            skill = matches[0]
            if os.path.exists(skill["file_path"]):
                return await self.sandbox.run_verified_skill(
                    task_id=task_id, skill_path=skill["file_path"], args=subtask.get("args")
                )

        # Step 2: No suitable tool found -> Activate Tool Generator & Refiner Loop (max 3 attempts)
        feedback_history: List[Dict[str, Any]] = []
        for attempt in range(1, 4):
            generated = await self.llm.synthesize_python_tool(
                subtask_description=task_desc,
                os_context=self.sandbox.get_os_profile(),
                prior_failures=feedback_history
            )
            tool_name = generated["tool_name"]
            tool_code = generated["code"]
            candidate_path = self.skill_dir / f"_candidate_{tool_name}.py"
            candidate_path.write_text(tool_code, encoding="utf-8")

            # Step 3: Execute inside isolated kernel sandbox with Git checkpointing
            exec_result = await self.sandbox.run_with_checkpoint(
                task_id=f"{task_id}-try{attempt}",
                script_path=str(candidate_path)
            )

            # Step 4: Critic evaluates execution outcome and scores tool reusability (0-10)
            evaluation = await self.llm.critic_evaluate_tool(
                subtask_description=task_desc,
                tool_code=tool_code,
                exec_stdout=exec_result.get("stdout", ""),
                exec_stderr=exec_result.get("stderr", ""),
                exit_code=exec_result.get("exit_code", -1)
            )

            if evaluation["task_completed"]:
                # Step 5: Crystallize tools scoring > 8 into permanent Procedural Memory
                crystallized = False
                if evaluation["reusability_score"] > 8:
                    final_path = self.skill_dir / f"{tool_name}.py"
                    if candidate_path.exists():
                        candidate_path.replace(final_path)
                    await self.vdb.index_new_skill(
                        tool_name=tool_name,
                        docstring=generated["docstring"],
                        file_path=str(final_path),
                        score=evaluation["reusability_score"],
                        atlas_pamphlet=evaluation["procedural_pamphlet"]
                    )
                    crystallized = True
                elif candidate_path.exists():
                    candidate_path.unlink()

                return {
                    "status": "SUCCESS",
                    "output": exec_result.get("stdout", ""),
                    "reusability_score": evaluation["reusability_score"],
                    "crystallized": crystallized
                }

            # Step 6: Refiner collects critic feedback for next self-correction iteration
            feedback_history.append({
                "attempt": attempt,
                "error_type": evaluation.get("error_type", "ExecutionError"),
                "critique": evaluation.get("critique", "Tool failed execution."),
                "stderr": exec_result.get("stderr", "")
            })
            if candidate_path.exists():
                candidate_path.unlink()

        return {
            "status": "FAILED",
            "reason": "Max 3 self-correction attempts exhausted.",
            "history": feedback_history
        }
