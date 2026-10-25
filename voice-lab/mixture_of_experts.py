r"""
System-Level Mixture of Experts (MoE) & Hermes Bridge (Phase 4)
Provides:
1. Gating Router: Classifies incoming queries and dispatches to specialized domain experts:
   - Expert 1: Algorithm & CS Scientist (First-principles, AST verification, Big-O analysis, LeetCode patterns)
   - Expert 2: OS & Visual Operator (Chrome tabs, Claude AI prompt, PowerShell, system telemetry)
   - Expert 3: Strategic News Intelligence (1-10 Importance scoring matrix, prioritized geopolitical reports)
2. Hermes Agent Bridge: Integrates local Hermes Agent (C:\Users\soham\AppData\Local\hermes\bin\hermes.exe)
   and inspects 51+ local skills for autonomous synthesis into assistant_memory/learned_skills.json.
"""
import os
import sys
import json
import re
import ast
import subprocess
import urllib.request
import xml.etree.ElementTree as ET
from typing import Dict, Any, List, Optional

class HermesBridge:
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
        """Lists installed Hermes skills from manifest or directory."""
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

        # Fallback to directory scan
        if os.path.isdir(self.skills_dir):
            for cat in os.listdir(self.skills_dir):
                cat_path = os.path.join(self.skills_dir, cat)
                if os.path.isdir(cat_path) and not cat.startswith("."):
                    skills.append({"name": cat, "category": "category", "description": f"Hermes {cat} skill domain"})
        return skills

    def save_learned_skill(self, skill_name: str, code: str, description: str, memory_file: str) -> bool:
        """Saves a synthesized skill to assistant memory in JSON list compatibility format."""
        import time
        try:
            os.makedirs(os.path.dirname(memory_file), exist_ok=True)
            data = []
            if os.path.isfile(memory_file):
                try:
                    with open(memory_file, "r", encoding="utf-8") as f:
                        loaded = json.load(f)
                    if isinstance(loaded, list):
                        data = loaded
                    elif isinstance(loaded, dict):
                        data = list(loaded.values())
                except Exception:
                    data = []

            skill_entry = {
                "intent": skill_name,
                "action_type": "hermes_skill",
                "code_or_cmd": code,
                "notes": description,
                "timestamp": time.time()
            }
            data.append(skill_entry)

            with open(memory_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            print(f"[!] save_learned_skill error: {e}")
            return False

class CSScientistExpert:
    """Expert 1: Elite Computer Science Professor & Algorithm Specialist."""
    SYSTEM_PROMPT = (
        "You are an Elite Computer Science Professor and Competitive Programming Scientist. "
        "For any algorithmic problem (graphs, dynamic programming, trees, sorting, Dijkstra, backtracking), "
        "you provide deep, first-principles intuition BEFORE writing the code. "
        "Analyze the exact time complexity O(...) and space complexity O(...). "
        "Write clean, idiomatic, and robust code (Python/C++). "
        "Keep your conversational overview punchy and direct for the user."
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
        score = 5 # baseline score
        for kw, weight in self.CRITICAL_KEYWORDS.items():
            if re.search(r"\b" + re.escape(kw) + r"\b", lower):
                score += weight // 2
        for kw, penalty in self.TRIVIA_KEYWORDS.items():
            if re.search(r"\b" + re.escape(kw) + r"\b", lower):
                score += penalty
        return max(1, min(10, score))

    def fetch_prioritized_news(self, topic: str = "top headlines", max_items: int = 5) -> str:
        """Fetches live news, scores each item via Importance Matrix, and returns sorted intelligence."""
        clean_topic = topic.strip()
        encoded = urllib.parse.quote(clean_topic)
        url = f"https://news.google.com/rss/search?q={encoded}&hl=en-IN&gl=IN&ceid=IN:en"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
            with urllib.request.urlopen(req, timeout=4.5) as resp:
                root = ET.fromstring(resp.read())
                items = root.findall(".//item")
                if not items:
                    return f"No live news reports found for '{clean_topic}'."

                scored_items = []
                for item in items[:12]:
                    title_elem = item.find("title")
                    title = title_elem.text if title_elem is not None else "Untitled"
                    clean_title = title.split(" - ")[0].strip()
                    score = self.score_importance(clean_title)
                    scored_items.append((score, clean_title))

                # Sort by Importance Score descending (critical events first, trivia penalized)
                scored_items.sort(key=lambda x: x[0], reverse=True)

                out = [f"Strategic Intelligence Feed for '{clean_topic}' (Prioritized 1-10):"]
                for i, (score, t) in enumerate(scored_items[:max_items], 1):
                    tag = "🚨 CRITICAL" if score >= 8 else ("📈 STRATEGIC" if score >= 6 else "ℹ️ NOTABLE")
                    out.append(f"  {i}. [{tag} | Score: {score}/10] {t}")

                return "\n".join(out)
        except Exception as e:
            return f"Error retrieving strategic intelligence: {e}"

class MoEGatingRouter:
    """System-Level Gating Router for Mixture of Experts."""
    def __init__(self):
        self.cs_expert = CSScientistExpert()
        self.news_expert = StrategicNewsExpert()
        self.hermes = HermesBridge()

        # Keywords for domain routing
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
        """Classifies user request and directs to the optimal Expert Agent."""
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
                    "model": "nandhank/qwen3.5-abliterated-truthful:9b", # Heavy reasoning expert
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

        # 4. OS & Visual Operator check
        for pat in self.os_patterns:
            if re.search(pat, lower):
                return {
                    "expert": "OS_OPERATOR",
                    "model": "qwen2.5:3b", # Fast tool model
                    "description": "Expert 2: OS & Visual Operator (Chrome, Claude, SystemController)",
                    "handler": "os_operator"
                }

        # 5. Default General Conversationalist
        return {
            "expert": "GENERAL_ASSISTANT",
            "model": "qwen2.5:3b",
            "description": "Conversational Assistant",
            "handler": "general"
        }

if __name__ == "__main__":
    router = MoEGatingRouter()
    queries = [
        "How do you implement Dijkstra algorithm with a priority queue in Python?",
        "Open a new tab in Chrome for GitHub",
        "Give me the latest news on international trade and border relations",
        "List all Hermes agent skills"
    ]
    print("Testing Mixture of Experts Gating Router:")
    for q in queries:
        r = router.route(q)
        print(f"\nQuery: '{q}'")
        print(f"  -> Routed to: {r['expert']} ({r['model']})")
