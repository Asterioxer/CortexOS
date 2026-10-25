"""
CortexOS Mixture of Experts (MoE) & Hermes Bridge Subsystem.
Absorbed and modernized from Voice Lab.

Features:
1. MoEGatingRouter:
   - Routes incoming user queries to the optimal local LLM expert based on intent and domain.
   - Expert 1: CS & Algorithm Scientist (AST syntax validation, Big-O complexity, LeetCode patterns).
   - Expert 2: OS & Somatosensory Operator (Desktop actions, Chrome tabs, PowerShell, files).
   - Expert 3: Strategic News & Intelligence Analyst (1-10 Importance scoring matrix).
2. HermesBridge:
   - Interfaces with local Hermes Agent CLI (C:\\Users\\soham\\AppData\\Local\\hermes\\bin\\hermes.exe).
   - Inspects installed skills and synthesizes skills into the Cortex memory substrate.
"""

import os
import sys
import json
import re
import ast
import subprocess
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from typing import Dict, Any, List, Optional


class HermesBridge:
    """Bridge to local Hermes Agent executable and skill definitions."""
    def __init__(self, hermes_root: str = r"C:\Users\soham\AppData\Local\hermes"):
        self.hermes_root = hermes_root
        self.hermes_bin = os.path.join(hermes_root, "bin", "hermes.exe")
        self.skills_dir = os.path.join(hermes_root, "skills")
        self.manifest_path = os.path.join(hermes_root, ".skills_prompt_snapshot.json")

    def is_available(self) -> bool:
        """Checks if local Hermes agent executable is available."""
        return os.path.isfile(self.hermes_bin)

    def get_version(self) -> str:
        """Retrieves Hermes agent version."""
        if not self.is_available():
            return "Hermes agent not installed."
        try:
            res = subprocess.run([self.hermes_bin, "--version"], capture_output=True, text=True, timeout=5)
            return res.stdout.strip() or res.stderr.strip()
        except Exception as e:
            return f"Error querying Hermes: {e}"

    def list_skills(self) -> List[Dict[str, str]]:
        """Lists installed Hermes skills from manifest or directory scan."""
        skills = []
        if os.path.isfile(self.manifest_path):
            try:
                with open(self.manifest_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for item in data.get("skills", []):
                    s_name = item.get("skill_name") or item.get("frontmatter_name") or item.get("name", "")
                    if s_name:
                        skills.append({
                            "name": s_name,
                            "category": item.get("category", ""),
                            "description": item.get("description", "")
                        })
                if skills:
                    return skills
            except Exception:
                pass

        if os.path.isdir(self.skills_dir):
            for cat in os.listdir(self.skills_dir):
                cat_path = os.path.join(self.skills_dir, cat)
                if os.path.isdir(cat_path) and not cat.startswith("."):
                    skills.append({"name": cat, "category": "domain", "description": f"Hermes {cat} skill domain"})
        return skills


class CSScientistExpert:
    """Expert 1: Elite Computer Science Professor & Algorithm Specialist."""
    SYSTEM_PROMPT = (
        "You are an Elite Computer Science Professor and Competitive Programming Scientist. "
        "For any algorithmic problem (graphs, dynamic programming, trees, sorting, Dijkstra, backtracking), "
        "provide deep, first-principles intuition BEFORE writing the code. "
        "Analyze the exact time complexity O(...) and space complexity O(...). "
        "Write clean, idiomatic, and robust code (Python/C++)."
    )

    def validate_code_ast(self, code_str: str) -> Dict[str, Any]:
        """Validates Python code syntax via AST parser."""
        try:
            tree = ast.parse(code_str)
            return {"valid": True, "error": None, "ast_nodes": len(tree.body)}
        except SyntaxError as se:
            return {"valid": False, "error": f"Syntax error at line {se.lineno}: {se.msg}"}


class StrategicNewsExpert:
    """Expert 3: Strategic News & Intelligence Analyst with 1-10 Importance Matrix."""
    CRITICAL_KEYWORDS = {
        "war": 9, "conflict": 8, "missile": 9, "treaty": 8, "sanction": 8,
        "election": 7, "inflation": 7, "interest rate": 7, "economy": 7,
        "prime minister": 7, "president": 7, "border": 8, "china": 8, "ai": 8,
        "semiconductor": 8, "nuclear": 9, "security": 7, "gdp": 7,
        "trade": 6, "court": 6, "supreme court": 7
    }
    TRIVIA_KEYWORDS = {
        "actor": -3, "actress": -3, "movie": -3, "box office": -3,
        "celebrity": -4, "dating": -4, "spotted": -4, "wedding": -3
    }

    def score_importance(self, title: str) -> int:
        """Scores news item from 1 to 10 based on geopolitical & economic weight."""
        lower = title.lower()
        score = 5
        for kw, weight in self.CRITICAL_KEYWORDS.items():
            if re.search(r"\b" + re.escape(kw) + r"\b", lower):
                score += weight // 2
        for kw, penalty in self.TRIVIA_KEYWORDS.items():
            if re.search(r"\b" + re.escape(kw) + r"\b", lower):
                score += penalty
        return max(1, min(10, score))


class MoEGatingRouter:
    """System-Level Gating Router for CortexOS Mixture of Experts."""
    def __init__(self):
        self.cs_expert = CSScientistExpert()
        self.news_expert = StrategicNewsExpert()
        self.hermes = HermesBridge()

        self.cs_patterns = [
            r"\b(algorithm|dijkstra|leetcode|dynamic programming|dp|big-o|time complexity|space complexity|binary search|bfs|dfs|graph|tree|sorting|quick sort|merge sort|recursion|hash map|trie|linked list|pointer|memory leak|ast|compiler)\b",
            r"\b(write a python function|write a c\+\+ function|how to implement|explain the intuition|solve leetcode|time and space complexity)\b"
        ]
        self.os_patterns = [
            r"\b(chrome|claude|tab|screenshot|desktop|mute|volume|powershell|notepad|open|close|launch|kill process|folder|file|battery|cpu|ram)\b"
        ]
        self.news_patterns = [
            r"\b(news|headline|geopolitics|election|war|border|foreign policy|economy|inflation|gdp|treaty|sanctions|market|stock)\b"
        ]
        self.hermes_patterns = [
            r"\b(hermes|agent skills|list skills|synthesize skill|hermes agent)\b"
        ]

    def route(self, query: str) -> Dict[str, Any]:
        """Classifies user request and directs to the optimal Expert Agent and local model."""
        lower = query.lower()

        # 1. Hermes Bridge check
        for pat in self.hermes_patterns:
            if re.search(pat, lower):
                return {
                    "expert": "HERMES_BRIDGE",
                    "model": "qwen2.5:3b",
                    "description": "Hermes Agent CLI & Autonomous Skills Domain",
                    "handler": "hermes"
                }

        # 2. Algorithm & CS Scientist check
        for pat in self.cs_patterns:
            if re.search(pat, lower):
                return {
                    "expert": "CS_SCIENTIST",
                    "model": "nandhank/qwen3.5-abliterated-truthful:9b",
                    "description": "Expert 1: Algorithm & CS Scientist (First-principles, AST verification)",
                    "handler": "cs_scientist"
                }

        # 3. Strategic News check
        for pat in self.news_patterns:
            if re.search(pat, lower):
                return {
                    "expert": "STRATEGIC_NEWS",
                    "model": "dolphinlabs/llama3.2-3b-uncensored:latest",
                    "description": "Expert 3: Strategic News Intelligence (1-10 Importance Matrix)",
                    "handler": "strategic_news"
                }

        # 4. OS & Somatosensory Operator check
        for pat in self.os_patterns:
            if re.search(pat, lower):
                return {
                    "expert": "OS_OPERATOR",
                    "model": "qwen2.5:3b",
                    "description": "Expert 2: OS & Somatosensory Operator",
                    "handler": "os_operator"
                }

        # 5. Default General Conversationalist
        return {
            "expert": "GENERAL_ASSISTANT",
            "model": "dolphinlabs/llama3.2-3b-uncensored:latest",
            "description": "Conversational Cognitive Assistant",
            "handler": "general"
        }
