#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "click>=8.0",
# ]
# ///
"""
Memory CLI - JSON-based Semantic Memory System

A structured memory system for Claude with schema-enforced entries.
Memory root: .claude/memories/ (relative to current directory)
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from uuid import uuid4

import click

MEMORY_ROOT = Path.cwd() / ".claude" / "memories"
INDEX_FILE = MEMORY_ROOT / "index.json"

VALID_CATEGORIES = ["preference", "fact", "context", "note"]
VALID_SUBJECTS = ["user", "project", "tool", "assistant", "other"]
VALID_SOURCES = ["explicit", "inferred", "observed"]


def get_memory_root() -> Path:
    MEMORY_ROOT.mkdir(parents=True, exist_ok=True)
    return MEMORY_ROOT


def generate_id() -> str:
    date_part = datetime.now().strftime("%Y%m%d")
    uuid_part = uuid4().hex[:8]
    return f"mem_{date_part}_{uuid_part}"


def create_memory_entry(
    content: str, category: str = "note", subject: str = "user",
    tags: List[str] = None, confidence: float = 1.0,
    source: str = "explicit", memory_id: str = None,
) -> Dict[str, Any]:
    now = datetime.now().isoformat()
    return {
        "id": memory_id or generate_id(),
        "category": category, "subject": subject,
        "content": content, "tags": tags or [],
        "confidence": max(0.0, min(1.0, confidence)),
        "source": source, "created_at": now, "updated_at": now,
    }


def validate_memory(memory: Dict[str, Any]) -> List[str]:
    errors = []
    if not memory.get("id"):
        errors.append("Missing 'id' field")
    if not memory.get("content"):
        errors.append("Missing 'content' field")
    if (cat := memory.get("category")) and cat not in VALID_CATEGORIES:
        errors.append(f"Invalid category '{cat}'. Must be one of: {VALID_CATEGORIES}")
    if (subj := memory.get("subject")) and subj not in VALID_SUBJECTS:
        errors.append(f"Invalid subject '{subj}'. Must be one of: {VALID_SUBJECTS}")
    if (src := memory.get("source")) and src not in VALID_SOURCES:
        errors.append(f"Invalid source '{src}'. Must be one of: {VALID_SOURCES}")
    conf = memory.get("confidence")
    if conf is not None and (not isinstance(conf, (int, float)) or conf < 0 or conf > 1):
        errors.append("Confidence must be a number between 0.0 and 1.0")
    return errors


def load_index() -> Dict[str, Any]:
    if not INDEX_FILE.exists():
        return {"memories": [], "version": "1.0"}
    with open(INDEX_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_index(index: Dict[str, Any]):
    get_memory_root()
    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(index, f, indent=2, ensure_ascii=False)


def add_memory_to_index(memory: Dict[str, Any]) -> bool:
    index = load_index()
    for existing in index["memories"]:
        if existing["id"] == memory["id"]:
            return False
    index["memories"].append(memory)
    save_index(index)
    return True


def update_memory_in_index(memory_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    index = load_index()
    for i, mem in enumerate(index["memories"]):
        if mem["id"] == memory_id:
            for key, value in updates.items():
                if key not in ("id", "created_at"):
                    mem[key] = value
            mem["updated_at"] = datetime.now().isoformat()
            index["memories"][i] = mem
            save_index(index)
            return mem
    return None


def delete_memory_from_index(memory_id: str) -> bool:
    index = load_index()
    for i, mem in enumerate(index["memories"]):
        if mem["id"] == memory_id:
            del index["memories"][i]
            save_index(index)
            return True
    return False


def get_memory_by_id(memory_id: str) -> Optional[Dict[str, Any]]:
    index = load_index()
    for mem in index["memories"]:
        if mem["id"] == memory_id:
            return mem
    return None


def find_memory_by_partial_id(partial_id: str) -> Optional[Dict[str, Any]]:
    index = load_index()
    matches = [m for m in index["memories"] if m["id"].startswith(partial_id) or partial_id in m["id"]]
    return matches[0] if len(matches) == 1 else None


def filter_memories(category=None, subject=None, tag=None, min_confidence=None, source=None):
    index = load_index()
    results = index["memories"]
    if category:
        results = [m for m in results if m.get("category") == category]
    if subject:
        results = [m for m in results if m.get("subject") == subject]
    if tag:
        results = [m for m in results if tag in m.get("tags", [])]
    if min_confidence is not None:
        results = [m for m in results if m.get("confidence", 0) >= min_confidence]
    if source:
        results = [m for m in results if m.get("source") == source]
    return results


def search_memories(query: str) -> List[Dict[str, Any]]:
    index = load_index()
    q = query.lower()
    return [
        m for m in index["memories"]
        if q in m.get("content", "").lower() or q in " ".join(m.get("tags", [])).lower()
    ]


@click.group()
@click.version_option(version="2.0.0")
def cli():
    """Memory CLI - JSON-based semantic memory for Claude."""
    pass


@cli.command()
@click.argument("content")
@click.option("--category", "-c", type=click.Choice(VALID_CATEGORIES), default="note")
@click.option("--subject", "-s", type=click.Choice(VALID_SUBJECTS), default="user")
@click.option("--tags", "-t", multiple=True)
@click.option("--confidence", "-conf", type=float, default=1.0)
@click.option("--source", type=click.Choice(VALID_SOURCES), default="explicit")
@click.option("--id", "memory_id", default=None)
def add(content, category, subject, tags, confidence, source, memory_id):
    """Add a new memory."""
    memory = create_memory_entry(content, category, subject, list(tags), confidence, source, memory_id)
    errors = validate_memory(memory)
    if errors:
        for e in errors:
            click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    if not add_memory_to_index(memory):
        raise click.ClickException(f"Memory with ID '{memory['id']}' already exists")
    click.echo(f"Memory added: {memory['id']}")


@cli.command("list")
@click.option("--category", "-c", type=click.Choice(VALID_CATEGORIES))
@click.option("--subject", "-s", type=click.Choice(VALID_SUBJECTS))
@click.option("--tag", "-t")
@click.option("--min-confidence", "-conf", type=float)
@click.option("--source", type=click.Choice(VALID_SOURCES))
@click.option("--limit", "-l", type=int, default=20)
@click.option("--json-output", "-j", is_flag=True)
def list_memories(category, subject, tag, min_confidence, source, limit, json_output):
    """List memories with optional filters."""
    memories = filter_memories(category, subject, tag, min_confidence, source)
    if not memories:
        click.echo("No memories found.")
        return
    memories.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
    memories = memories[:limit]
    if json_output:
        click.echo(json.dumps(memories, indent=2, ensure_ascii=False))
        return
    click.echo(f"Found {len(memories)} memories:\n")
    for mem in memories:
        conf = mem.get("confidence", 1.0)
        click.echo(f"[{mem['id']}] {mem.get('category', '?'):10} | {mem.get('subject', '?'):8} | {conf:.1f}")
        click.echo(f"  {mem.get('content', '')[:70]}{'...' if len(mem.get('content', '')) > 70 else ''}")
        if tags := mem.get("tags", []):
            click.echo(f"  Tags: {', '.join(tags)}")
        click.echo()


@cli.command()
@click.argument("memory_id")
@click.option("--json-output", "-j", is_flag=True)
def get(memory_id, json_output):
    """Get a memory by ID (supports partial match)."""
    memory = get_memory_by_id(memory_id) or find_memory_by_partial_id(memory_id)
    if not memory:
        raise click.ClickException(f"Memory not found: {memory_id}")
    if json_output:
        click.echo(json.dumps(memory, indent=2, ensure_ascii=False))
        return
    click.echo(f"Memory: {memory['id']}")
    click.echo("=" * 50)
    for k in ("category", "subject", "confidence", "source", "created_at", "updated_at"):
        click.echo(f"{k:12}: {memory.get(k, 'N/A')}")
    if tags := memory.get("tags", []):
        click.echo(f"{'tags':12}: {', '.join(tags)}")
    click.echo(f"\n{memory.get('content', '')}")


@cli.command()
@click.argument("memory_id")
@click.option("--content", "-c")
@click.option("--category", type=click.Choice(VALID_CATEGORIES))
@click.option("--subject", type=click.Choice(VALID_SUBJECTS))
@click.option("--tags", "-t", multiple=True)
@click.option("--confidence", "-conf", type=float)
@click.option("--source", type=click.Choice(VALID_SOURCES))
def update(memory_id, content, category, subject, tags, confidence, source):
    """Update an existing memory."""
    memory = get_memory_by_id(memory_id) or find_memory_by_partial_id(memory_id)
    if not memory:
        raise click.ClickException(f"Memory not found: {memory_id}")
    updates = {}
    if content is not None: updates["content"] = content
    if category is not None: updates["category"] = category
    if subject is not None: updates["subject"] = subject
    if tags: updates["tags"] = list(tags)
    if confidence is not None: updates["confidence"] = max(0.0, min(1.0, confidence))
    if source is not None: updates["source"] = source
    if not updates:
        raise click.ClickException("No updates provided")
    updated = update_memory_in_index(memory["id"], updates)
    if updated:
        click.echo(f"Memory updated: {updated['id']}")
    else:
        raise click.ClickException("Failed to update memory")


@cli.command()
@click.argument("memory_id")
@click.option("--force", "-f", is_flag=True)
def delete(memory_id, force):
    """Delete a memory."""
    memory = get_memory_by_id(memory_id) or find_memory_by_partial_id(memory_id)
    if not memory:
        raise click.ClickException(f"Memory not found: {memory_id}")
    if not force:
        click.echo(f"About to delete: {memory['id']}")
        click.echo(f"  Content: {memory.get('content', '')[:50]}...")
        if not click.confirm("Continue?"):
            click.echo("Cancelled.")
            return
    if delete_memory_from_index(memory["id"]):
        click.echo(f"Memory deleted: {memory['id']}")
    else:
        raise click.ClickException("Failed to delete memory")


@cli.command()
@click.argument("query")
@click.option("--limit", "-l", type=int, default=10)
@click.option("--json-output", "-j", is_flag=True)
def search(query, limit, json_output):
    """Search memories by content."""
    results = search_memories(query)[:limit]
    if not results:
        click.echo(f"No memories found for: {query}")
        return
    if json_output:
        click.echo(json.dumps(results, indent=2, ensure_ascii=False))
        return
    click.echo(f"Found {len(results)} memories matching '{query}':\n")
    for mem in results:
        click.echo(f"[{mem['id']}] {mem.get('category', '?')} | {mem.get('subject', '?')}")
        click.echo(f"  {mem.get('content', '')[:70]}")
        click.echo()


@cli.command()
def stats():
    """Show memory statistics."""
    index = load_index()
    memories = index.get("memories", [])
    if not memories:
        click.echo("No memories stored.")
        return
    by_cat = {}
    by_subj = {}
    all_tags = set()
    for m in memories:
        by_cat[m.get("category", "?")] = by_cat.get(m.get("category", "?"), 0) + 1
        by_subj[m.get("subject", "?")] = by_subj.get(m.get("subject", "?"), 0) + 1
        all_tags.update(m.get("tags", []))
    avg_conf = sum(m.get("confidence", 1.0) for m in memories) / len(memories)
    click.echo(f"Total: {len(memories)} | Avg confidence: {avg_conf:.2f} | Tags: {len(all_tags)}")
    click.echo(f"By category: {', '.join(f'{k}={v}' for k, v in sorted(by_cat.items()))}")
    click.echo(f"By subject:  {', '.join(f'{k}={v}' for k, v in sorted(by_subj.items()))}")
    if all_tags:
        click.echo(f"Tags: {', '.join(sorted(all_tags))}")


@cli.command("export")
@click.option("--pretty", "-p", is_flag=True)
def export_memories(pretty):
    """Export all memories as JSON."""
    index = load_index()
    click.echo(json.dumps(index, indent=2 if pretty else None, ensure_ascii=False))


@cli.command("import")
@click.argument("file", type=click.Path(exists=True))
@click.option("--merge", "-m", is_flag=True)
@click.option("--replace", "-r", is_flag=True)
def import_memories(file, merge, replace):
    """Import memories from a JSON file."""
    with open(file, "r", encoding="utf-8") as f:
        data = json.load(f)
    new_memories = data["memories"] if isinstance(data, dict) and "memories" in data else data if isinstance(data, list) else None
    if new_memories is None:
        raise click.ClickException("Invalid format. Expected {memories: [...]} or [...]")
    for mem in new_memories:
        if errors := validate_memory(mem):
            raise click.ClickException(f"Invalid memory {mem.get('id', '?')}: {errors}")
    if replace:
        save_index({"memories": new_memories, "version": "1.0"})
        click.echo(f"Replaced all. Imported {len(new_memories)} memories.")
    elif merge:
        index = load_index()
        existing_ids = {m["id"] for m in index["memories"]}
        added = sum(1 for m in new_memories if m["id"] not in existing_ids)
        index["memories"].extend(m for m in new_memories if m["id"] not in existing_ids)
        save_index(index)
        click.echo(f"Merged: {added} added, {len(new_memories) - added} skipped.")
    else:
        raise click.ClickException("Specify --merge or --replace")


@cli.command()
def clear():
    """Clear all memories (with confirmation)."""
    index = load_index()
    count = len(index.get("memories", []))
    if count == 0:
        click.echo("No memories to clear.")
        return
    click.echo(f"About to delete {count} memories.")
    if click.confirm("Are you sure?"):
        save_index({"memories": [], "version": "1.0"})
        click.echo(f"Cleared {count} memories.")
    else:
        click.echo("Cancelled.")


if __name__ == "__main__":
    cli()
