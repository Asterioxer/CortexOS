import os
import json
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from cortex.vault.vault_manager import ObsidianVault, get_vault
from cortex.vault.rag_engine import VaultRAG, get_vault_rag
from cortex.vault.git_sync import VaultSync, get_vault_sync
from cortex.vault.copilot_pair import PairCopilot, get_pair_copilot
from cortex.server import app

client = TestClient(app)


def test_vault_structure_and_notes():
    vault = get_vault()
    assert vault.vault_dir.exists()
    assert vault.obsidian_dir.exists()

    notes = vault.scan_notes(force=True)
    assert len(notes) >= 10
    assert "00_Index.md" in notes

    index_note = notes["00_Index.md"]
    assert index_note.title == "CortexOS Master Knowledge Vault (MOC)"
    assert len(index_note.wikilinks) > 0
    assert "cortex/moc" in index_note.tags


def test_note_crud_and_frontmatter(tmp_path):
    vault = ObsidianVault(vault_dir=tmp_path)
    # 1. Save note
    note = vault.save_note(
        rel_path="02_Pair_Programming/Test_Note.md",
        content="This is a test note with [[00_Index]] link and #cortex/test tag.",
        title="Test Grounded Note",
        frontmatter={"type": "test", "tags": ["cortex/test"]}
    )
    assert note.rel_path == "02_Pair_Programming/Test_Note.md"
    assert note.title == "Test Grounded Note"
    assert "00_Index" in note.wikilinks
    assert "cortex/test" in note.tags

    # 2. Get note
    fetched = vault.get_note("02_Pair_Programming/Test_Note.md")
    assert fetched is not None
    assert "This is a test note" in fetched.content

    # 3. List notes
    note_list = vault.list_notes(category="02_Pair_Programming")
    assert len(note_list) == 1
    assert note_list[0]["title"] == "Test Grounded Note"

    # 4. Delete note
    deleted = vault.delete_note("02_Pair_Programming/Test_Note.md")
    assert deleted is True
    assert vault.get_note("02_Pair_Programming/Test_Note.md") is None


def test_vault_graph_data():
    vault = get_vault()
    graph = vault.get_graph_data()
    assert "nodes" in graph
    assert "links" in graph
    assert len(graph["nodes"]) >= 10
    assert len(graph["links"]) > 0


def test_vault_rag_search_and_grounding():
    rag = get_vault_rag()
    results = rag.search("stallbreaker hardware gate timeout panic", top_k=3)
    assert len(results) > 0
    top = results[0]
    assert "stallbreaker" in top.note_title.lower() or "daemons" in top.note_title.lower()
    assert top.score > 0.0

    # Grounded prompt context
    ctx = rag.retrieve_grounded_context("stallbreaker timeout", top_k=2)
    assert "<grounded_obsidian_vault_knowledge>" in ctx
    assert "[SOURCE:" in ctx
    assert "</grounded_obsidian_vault_knowledge>" in ctx

    # Grounding verification
    v = rag.verify_grounding("StallBreaker sentinel monitors cognitive loop with 45.0s timeout")
    assert v["grounded"] is True
    assert v["confidence"] > 0.4


def test_vault_git_sync(tmp_path):
    sync = VaultSync(workspace_root=tmp_path, vault_dir=tmp_path / "cortex_vault")
    (tmp_path / "cortex_vault").mkdir(parents=True, exist_ok=True)
    test_note = tmp_path / "cortex_vault" / "test.md"
    test_note.write_text("# Test\nContent", encoding="utf-8")

    # 1. Init repo
    init_res = sync.init_repo()
    assert init_res["status"] == "SUCCESS"
    assert sync.is_initialized() is True

    # 2. Status
    st = sync.status()
    assert st["initialized"] is True
    assert st["status_label"] in ["SYNCED", "PENDING_CHANGES"]

    # 3. Local sync
    sync_res = sync.sync()
    assert sync_res["status"] in ["SYNCED", "LOCAL_BACKUP_ONLY", "NO_CHANGES"]
    assert sync.get_last_sync_time() is not None

    # 4. Zip backup export
    zip_path = sync.export_backup_zip()
    assert zip_path.exists()
    assert zip_path.suffix == ".zip"


@pytest.mark.asyncio
async def test_pair_copilot_execution():
    copilot = get_pair_copilot()

    # Test 1: Telemetry intent
    res = await copilot.execute_pair_request("check hardware telemetry")
    assert res["action_executed"]["type"] == "get_telemetry"
    assert "Hardware Posture:" in res["user_response"]
    assert len(res["grounded_sources"]) > 0

    # Test 2: Vault search intent
    search_res = await copilot.execute_pair_request("search vault stallbreaker")
    assert search_res["action_executed"]["type"] == "vault_search"
    assert len(search_res["action_result"]) > 0

    # Test 3: Note adding intent
    add_res = await copilot.execute_pair_request("add note: Verified system startup daemon on Windows 11")
    assert add_res["action_executed"]["type"] == "vault_add_note"
    assert "Recorded note to" in add_res["user_response"]


def test_api_vault_endpoints():
    # 1. Status
    res_st = client.get("/api/vault/status")
    assert res_st.status_code == 200
    st_data = res_st.json()
    assert "vault" in st_data
    assert "backup_git" in st_data
    assert st_data["vault"]["total_notes"] >= 10

    # 2. Notes List
    res_notes = client.get("/api/vault/notes")
    assert res_notes.status_code == 200
    notes_list = res_notes.json()
    assert len(notes_list) >= 10

    # 3. Get Note
    res_note = client.get("/api/vault/note?path=00_Index.md")
    assert res_note.status_code == 200
    note_data = res_note.json()
    assert "title" in note_data
    assert "CortexOS Master Knowledge Vault" in note_data["title"]

    # 4. RAG Search
    res_search = client.get("/api/vault/search?q=cognitive+pipeline")
    assert res_search.status_code == 200
    search_data = res_search.json()
    assert search_data["count"] > 0
    assert len(search_data["results"]) > 0

    # 5. Graph
    res_graph = client.get("/api/vault/graph")
    assert res_graph.status_code == 200
    graph_data = res_graph.json()
    assert "nodes" in graph_data
    assert "links" in graph_data

    # 6. Save Note
    res_save = client.post("/api/vault/note", json={
        "path": "02_Pair_Programming/Api_Test_Note.md",
        "title": "API Test Note",
        "content": "Created via FastAPI endpoint test.",
        "frontmatter": {"tags": ["cortex/test"]}
    })
    assert res_save.status_code == 200
    assert res_save.json()["status"] == "SUCCESS"

    # Clean up test note
    res_del = client.delete("/api/vault/note?path=02_Pair_Programming/Api_Test_Note.md")
    assert res_del.status_code == 200


@pytest.mark.asyncio
async def test_api_vault_pair_copilot():
    res = client.post("/api/vault/pair", json={"prompt": "telemetry"})
    assert res.status_code == 200
    data = res.json()
    assert data["action_executed"]["type"] == "get_telemetry"
    assert "Hardware Posture:" in data["user_response"]


def test_dashboard_vault_ui():
    res = client.get("/")
    assert res.status_code == 200
    html = res.text
    assert 'id="tab-vault"' in html
    assert 'id="pane-vault"' in html
    assert 'id="vault-notes-list"' in html
    assert 'id="vault-preview-area"' in html
    assert 'id="vault-rag-results"' in html
    assert 'id="vault-copilot-input"' in html
    assert 'id="vault-sync-badge"' in html
