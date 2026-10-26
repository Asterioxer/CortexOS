import os
import re
import time
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Set, Tuple
import yaml


@dataclass
class VaultNote:
    rel_path: str
    abs_path: Path
    title: str
    frontmatter: Dict[str, Any]
    content: str
    raw_text: str
    wikilinks: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    word_count: int = 0
    last_modified: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rel_path": self.rel_path,
            "title": self.title,
            "frontmatter": self.frontmatter,
            "wikilinks": self.wikilinks,
            "tags": self.tags,
            "word_count": self.word_count,
            "last_modified": self.last_modified
        }


class ObsidianVault:
    """Manages the local Obsidian Markdown Knowledge Vault for CortexOS."""

    WIKILINK_REGEX = re.compile(r"\[\[([^\]\|]+)(?:\|([^\]]+))?\]\]")
    TAG_REGEX = re.compile(r"(?:^|\s)#([a-zA-Z0-9_\-\/]+)")
    FRONTMATTER_REGEX = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)

    def __init__(self, vault_dir: Optional[Path] = None):
        if vault_dir is None:
            # Default to cortex_vault/ in project root
            workspace_root = Path(__file__).resolve().parent.parent.parent
            self.vault_dir = (workspace_root / "cortex_vault").resolve()
        else:
            self.vault_dir = Path(vault_dir).resolve()

        self.obsidian_dir = self.vault_dir / ".obsidian"
        self._notes_cache: Dict[str, VaultNote] = {}
        self._last_scan_time: float = 0.0
        self.ensure_vault_structure()

    @property
    def vault_path(self) -> Path:
        """Alias for vault_dir for compatibility."""
        return self.vault_dir

    def ensure_vault_structure(self) -> None:
        """Ensures that essential directories and Obsidian config files exist."""
        self.vault_dir.mkdir(parents=True, exist_ok=True)
        self.obsidian_dir.mkdir(parents=True, exist_ok=True)

        for subfolder in [
            "01_Architecture",
            "02_Pair_Programming",
            "03_Decisions_ADR",
            "04_Skills_Catalog",
            "05_System_State"
        ]:
            (self.vault_dir / subfolder).mkdir(parents=True, exist_ok=True)

        app_json = self.obsidian_dir / "app.json"
        if not app_json.exists():
            app_json.write_text('{"livePreview": true, "useTab": true, "tabSize": 2}', encoding="utf-8")

    def parse_note_file(self, file_path: Path) -> VaultNote:
        """Parses a markdown file, extracting YAML frontmatter, wikilinks, and tags."""
        raw_text = file_path.read_text(encoding="utf-8", errors="replace")
        rel_path = file_path.relative_to(self.vault_dir).as_posix()

        frontmatter: Dict[str, Any] = {}
        content = raw_text

        fm_match = self.FRONTMATTER_REGEX.match(raw_text)
        if fm_match:
            yaml_block = fm_match.group(1)
            try:
                frontmatter = yaml.safe_load(yaml_block) or {}
            except Exception:
                frontmatter = {}
            content = raw_text[fm_match.end():]

        # Extract title from frontmatter or first H1 or filename
        title = frontmatter.get("title")
        if not title:
            for line in content.splitlines():
                line_s = line.strip()
                if line_s.startswith("# "):
                    title = line_s.lstrip("# ").strip()
                    break
        if not title:
            title = file_path.stem.replace("_", " ")

        # Extract wikilinks [[Target]]
        wikilinks: List[str] = []
        for match in self.WIKILINK_REGEX.finditer(content):
            target = match.group(1).strip()
            if target not in wikilinks:
                wikilinks.append(target)

        # Extract tags (from frontmatter tags list + inline #tags)
        tags_set: Set[str] = set()
        fm_tags = frontmatter.get("tags", [])
        if isinstance(fm_tags, list):
            tags_set.update(str(t).lstrip("#") for t in fm_tags)
        elif isinstance(fm_tags, str):
            tags_set.add(fm_tags.lstrip("#"))

        for match in self.TAG_REGEX.finditer(content):
            t = match.group(1).strip()
            if not t.isdigit():
                tags_set.add(t)

        word_count = len(re.findall(r"\w+", content))
        mtime = file_path.stat().st_mtime

        return VaultNote(
            rel_path=rel_path,
            abs_path=file_path,
            title=str(title),
            frontmatter=frontmatter,
            content=content.strip(),
            raw_text=raw_text,
            wikilinks=wikilinks,
            tags=sorted(list(tags_set)),
            word_count=word_count,
            last_modified=mtime
        )

    def scan_notes(self, force: bool = False) -> Dict[str, VaultNote]:
        """Scans the vault directory for markdown notes, caching results."""
        current_time = time.time()
        if not force and self._notes_cache and (current_time - self._last_scan_time < 2.0):
            return self._notes_cache

        notes: Dict[str, VaultNote] = {}
        for root, dirs, files in os.walk(self.vault_dir):
            # Ignore .obsidian and hidden directories
            dirs[:] = [d for d in dirs if not d.startswith(".")]
            for f in files:
                if f.endswith(".md"):
                    full_p = Path(root) / f
                    try:
                        note = self.parse_note_file(full_p)
                        notes[note.rel_path] = note
                    except Exception:
                        pass

        self._notes_cache = notes
        self._last_scan_time = current_time
        return self._notes_cache

    def get_note(self, rel_path: str) -> Optional[VaultNote]:
        """Retrieves a note by relative path or stem."""
        notes = self.scan_notes()
        norm_rel = rel_path.replace("\\", "/").strip("/")
        if not norm_rel.endswith(".md"):
            norm_rel_md = f"{norm_rel}.md"
        else:
            norm_rel_md = norm_rel

        if norm_rel_md in notes:
            return notes[norm_rel_md]

        # Fallback: search by stem or filename
        stem = Path(norm_rel).stem.lower()
        for k, n in notes.items():
            if Path(k).stem.lower() == stem or n.title.lower() == stem:
                return n
        return None

    def save_note(
        self,
        rel_path: str,
        content: str,
        frontmatter: Optional[Dict[str, Any]] = None,
        title: Optional[str] = None
    ) -> VaultNote:
        """Saves or updates a markdown note in the vault."""
        norm_rel = rel_path.replace("\\", "/").strip("/")
        if not norm_rel.endswith(".md"):
            norm_rel = f"{norm_rel}.md"

        target_file = self.vault_dir / norm_rel
        target_file.parent.mkdir(parents=True, exist_ok=True)

        fm = frontmatter or {}
        if title and "title" not in fm:
            fm["title"] = title
        if "last_updated" not in fm:
            fm["last_updated"] = time.strftime("%Y-%m-%d")

        # Format YAML frontmatter
        fm_yaml = yaml.dump(fm, default_flow_style=False, sort_keys=False).strip()
        full_text = f"---\n{fm_yaml}\n---\n\n{content.strip()}\n"

        target_file.write_text(full_text, encoding="utf-8")
        note = self.parse_note_file(target_file)
        self._notes_cache[note.rel_path] = note
        return note

    def delete_note(self, rel_path: str) -> bool:
        """Deletes a note from the vault."""
        note = self.get_note(rel_path)
        if not note or not note.abs_path.exists():
            return False
        try:
            note.abs_path.unlink()
            if note.rel_path in self._notes_cache:
                del self._notes_cache[note.rel_path]
            return True
        except Exception:
            return False

    def list_notes(
        self,
        category: Optional[str] = None,
        tag: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Returns filtered list of note descriptors."""
        notes = self.scan_notes()
        res = []
        for n in notes.values():
            if category:
                cat_norm = category.lower().strip("/")
                if not n.rel_path.lower().startswith(cat_norm):
                    continue
            if tag:
                tag_norm = tag.lower().lstrip("#")
                if not any(t.lower() == tag_norm or t.lower().startswith(f"{tag_norm}/") for t in n.tags):
                    continue
            res.append(n.to_dict())

        return sorted(res, key=lambda x: x["rel_path"])

    def get_graph_data(self) -> Dict[str, Any]:
        """Generates graph topology data (nodes and links) for Obsidian-style graph views."""
        notes = self.scan_notes()
        nodes = []
        links = []

        path_to_id: Dict[str, str] = {}
        for n in notes.values():
            path_to_id[n.rel_path] = n.rel_path
            path_to_id[Path(n.rel_path).stem] = n.rel_path

            category = n.rel_path.split("/")[0] if "/" in n.rel_path else "root"
            nodes.append({
                "id": n.rel_path,
                "label": n.title,
                "category": category,
                "tags": n.tags,
                "word_count": n.word_count
            })

        for n in notes.values():
            for link in n.wikilinks:
                target_norm = link.replace("\\", "/").strip("/")
                if target_norm in path_to_id:
                    links.append({
                        "source": n.rel_path,
                        "target": path_to_id[target_norm]
                    })
                else:
                    # Match by stem
                    stem = Path(target_norm).stem
                    if stem in path_to_id:
                        links.append({
                            "source": n.rel_path,
                            "target": path_to_id[stem]
                        })

        return {"nodes": nodes, "links": links}

    def get_stats(self) -> Dict[str, Any]:
        """Returns aggregate vault metrics."""
        notes = self.scan_notes()
        total_words = sum(n.word_count for n in notes.values())
        all_tags: Set[str] = set()
        categories: Set[str] = set()

        for n in notes.values():
            all_tags.update(n.tags)
            if "/" in n.rel_path:
                categories.add(n.rel_path.split("/")[0])

        return {
            "total_notes": len(notes),
            "total_words": total_words,
            "categories": sorted(list(categories)),
            "tags": sorted(list(all_tags)),
            "vault_path": str(self.vault_dir)
        }

    def update_active_context(self, active_goal: str, details: Optional[Dict[str, Any]] = None) -> None:
        """Dynamically logs live milestone context into 02_Pair_Programming/Active_Context.md."""
        ctx_file = self.vault_dir / "02_Pair_Programming" / "Active_Context.md"
        now_str = time.strftime("%Y-%m-%d %H:%M:%S")

        details_str = ""
        if details:
            for k, v in details.items():
                details_str += f"- **{k}**: {v}\n"

        content = f"""# 📍 Active Living Context

## Current Milestone: {active_goal}
- **Timestamp**: {now_str}
{details_str}

## Live Memory Substrate
- Synchronized with CortexOS GWA cognitive tick and pair programming copilot.
"""
        fm = {
            "title": "Active Living Context",
            "type": "pair_programming",
            "tags": ["cortex/active_context", "cortex/status"],
            "last_updated": time.strftime("%Y-%m-%d")
        }
        self.save_note("02_Pair_Programming/Active_Context.md", content, frontmatter=fm)


_GLOBAL_VAULT: Optional[ObsidianVault] = None


def get_vault() -> ObsidianVault:
    global _GLOBAL_VAULT
    if _GLOBAL_VAULT is None:
        _GLOBAL_VAULT = ObsidianVault()
    return _GLOBAL_VAULT
